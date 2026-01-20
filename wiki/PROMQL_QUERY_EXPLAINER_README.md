# PromQL Query Explainer Agent

A semantic validation agent that explains what a generated PromQL query does and validates whether it matches the original user intent.

## Overview

The **PromQLQueryExplainerAgent** uses LLM intelligence to:

1. **Explain** what a generated PromQL query actually does
2. **Summarize** the original query intent
3. **Compare** them semantically to determine if they match
4. **Return** a structured validation result with confidence score

This agent is crucial for ensuring that query generation systems produce queries that truly reflect user intentions, catching subtle semantic mismatches that syntax validation alone would miss.

## Architecture

```
validation_engine/
├── agent/
│   └── metrics/
│       ├── promql_query_explainer_agent.py    # Main agent implementation
│       └── promql_metricname_extractor_agent.py
├── metrics/
│   └── structured_outputs.py                   # SemanticValidationResult model
└── prompts/
    └── agent/
        └── metrics/
            └── PROMQL_QUERY_EXPLAINER_AGENT_INSTRUCTIONS.md  # LLM system prompt
```

## Components

### 1. PromQLQueryExplainerAgent

**Location:** `codd_engine/validation_engine/agent/metrics/promql_query_explainer_agent.py`

**Main Methods:**

```python
def validate_semantic_match(
    self,
    original_intent: MetricsQueryIntent,
    generated_query: str
) -> SemanticValidationResult:
    """
    Validate whether a generated PromQL query matches the original intent.

    Args:
        original_intent: The original metrics query intent
        generated_query: The generated PromQL query string

    Returns:
        SemanticValidationResult with match status, explanation, and confidence
    """

def explain_query(self, promql_query: str) -> str:
    """
    Explain what a PromQL query does in plain language.

    Args:
        promql_query: The PromQL query to explain

    Returns:
        Plain language explanation of the query
    """
```

### 2. SemanticValidationResult

**Location:** `codd_engine/validation_engine/metrics/structured_outputs.py`

**Structure:**

```python
class SemanticValidationResult(BaseModel):
    """Response schema for semantic validation of PromQL query intent."""

    intent_match: bool                     # Does the query fully match the intent?
    partial_match: bool                    # Does the query partially match (minor deviations)?
    explanation: str                       # Why they match, partially match, or don't match
    original_intent_summary: str           # Summary of what user wanted
    actual_query_behavior: str             # Description of what query does
    confidence: float                      # Confidence score (0.0 to 1.0)
```

**Match Types:**

- **Full Match** (`intent_match=True, partial_match=False`): Query perfectly matches the intent with no significant deviations
- **Partial Match** (`intent_match=False, partial_match=True`): Core intent achieved but with minor deviations such as:
  - Slightly different percentile values (e.g., 99th vs 95th)
  - Missing optional filters (core intent still achieved)
  - Minor time window variations (e.g., 4m vs 5m)
  - Additional grouping dimensions that don't change core semantics
- **No Match** (`intent_match=False, partial_match=False`): Query fundamentally doesn't match the intent

### 3. System Prompt

**Location:** `codd_engine/prompts/agent/metrics/PROMQL_QUERY_EXPLAINER_AGENT_INSTRUCTIONS.md`

The system prompt instructs the LLM to:
- Analyze PromQL query components (metric, filters, aggregations, time windows, grouping)
- Consider metric type appropriateness (counter vs gauge vs histogram)
- Compare semantic intent vs actual behavior
- Provide detailed explanations with confidence scores

## Usage

### Basic Usage

```python
from codd_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from codd_engine.validation_engine import (
    PromQLQueryExplainerAgent,
    SemanticValidationResult,
)
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

# Initialize the agent
config_manager = ConfigManager()
instructions_manager = InstructionsManager()
explainer = PromQLQueryExplainerAgent(config_manager, instructions_manager)

# Define original intent
intent = MetricsQueryIntent(
    metric="http_requests_total",
    metric_type="counter",
    filters={"status": "500"},
    window="5m",
    aggregation_suggestions=[
        AggregationFunctionSuggestion(function_name="rate")
    ]
)

# Generated query to validate
generated_query = 'rate(http_requests_total{status="500"}[5m])'

# Validate semantic match
result = explainer.validate_semantic_match(intent, generated_query)

print(f"Intent Match: {result.intent_match}")
print(f"Partial Match: {result.partial_match}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Explanation: {result.explanation}")
```

### Example: Matching Intent

```python
# Intent: Calculate rate of HTTP 500 errors
intent = MetricsQueryIntent(
    metric="http_requests_total",
    metric_type="counter",
    filters={"status": "500"},
    window="5m",
    aggregation_suggestions=[AggregationFunctionSuggestion(function_name="rate")]
)

# Query: Correctly uses rate() on counter
query = 'rate(http_requests_total{status="500"}[5m])'

result = explainer.validate_semantic_match(intent, query)
# result.intent_match == True
# result.partial_match == False
# result.confidence ~= 0.95
```

### Example: Mismatched Intent

```python
# Intent: Calculate average memory usage (gauge metric)
intent = MetricsQueryIntent(
    metric="memory_usage_bytes",
    metric_type="gauge",
    window="5m",
    aggregation_suggestions=[
        AggregationFunctionSuggestion(function_name="avg_over_time")
    ]
)

# Query: INCORRECTLY uses rate() on a gauge
query = "rate(memory_usage_bytes[5m])"

result = explainer.validate_semantic_match(intent, query)
# result.intent_match == False
# result.partial_match == False
# result.explanation mentions that rate() is incorrect for gauges
```

### Example: Partial Match

```python
# Intent: Calculate 95th percentile latency
intent = MetricsQueryIntent(
    metric="api_latency_seconds",
    metric_type="histogram",
    filters={"endpoint": "/users"},
    window="5m",
    aggregation_suggestions=[
        AggregationFunctionSuggestion(
            function_name="histogram_quantile",
            params={"quantile": 0.95}
        )
    ]
)

# Query: Uses 99th percentile instead of 95th
query = 'histogram_quantile(0.99, rate(api_latency_seconds_bucket{endpoint="/users"}[5m]))'

result = explainer.validate_semantic_match(intent, query)
# result.intent_match == False
# result.partial_match == True  # Core structure correct, but wrong percentile
# result.confidence ~= 0.85
```

### Example: Full Match - Histogram with Percentile

```python
intent = MetricsQueryIntent(
    metric="api_latency_seconds",
    metric_type="histogram",
    filters={"endpoint": "/users"},
    window="5m",
    group_by=["instance"],
    aggregation_suggestions=[
        AggregationFunctionSuggestion(
            function_name="histogram_quantile",
            params={"quantile": 0.95}
        )
    ]
)

query = '''histogram_quantile(0.95,
    rate(api_latency_seconds_bucket{endpoint="/users"}[5m])
) by (instance)'''

result = explainer.validate_semantic_match(intent, query)
# result.intent_match == True
# result.partial_match == False
```

### Example: Just Explain a Query

```python
query = 'sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))'

explanation = explainer.explain_query(query)
# Returns plain language explanation of what the query does
```

## Validation Logic

The agent considers multiple aspects when validating semantic match:

### 1. Metric Selection
- Does the query use the correct metric name?
- Are all specified metrics included?

### 2. Filters/Label Selectors
- Are label matchers correctly applied?
- Do they match the intent's filter requirements?

### 3. Time Windows
- Is the time range appropriate?
- Does it match the specified window (e.g., `[5m]`)?

### 4. Aggregation Functions
- **Counter metrics**: Should use `rate()`, `increase()`, or `irate()`
- **Gauge metrics**: Should use instant values or `_over_time()` functions
- **Histogram metrics**: Should use `histogram_quantile()` for percentiles
- Is the chosen aggregation appropriate for the metric type?

### 5. Grouping Dimensions
- Are `by` or `without` clauses correct?
- Do they match the requested group_by dimensions?

### 6. Overall Semantics
- Does the query compute what the user intended?
- Are there any subtle mismatches in the logic?

## Metric Type Considerations

The agent understands that different metric types require different aggregation functions:

| Metric Type | Appropriate Aggregations | Inappropriate Aggregations |
|-------------|-------------------------|---------------------------|
| Counter | `rate()`, `increase()`, `irate()` | `avg_over_time()` (on raw counter) |
| Gauge | `avg_over_time()`, `max_over_time()`, `min_over_time()`, instant values | `rate()`, `increase()` |
| Histogram | `histogram_quantile()`, `rate()` (on buckets) | `rate()` on raw histogram |
| Summary | `avg_over_time()`, quantile labels | N/A |
| Timer | `histogram_quantile()`, `rate()` | N/A |

## Error Handling

The agent raises `SemanticValidationError` in these cases:

```python
from codd_engine.validation_engine import SemanticValidationError

try:
    result = explainer.validate_semantic_match(intent, query)
except SemanticValidationError as e:
    # Handle validation errors:
    # - Empty query
    # - Intent without metric
    # - LLM API failures
    print(f"Validation failed: {e}")
```

## Integration with Query Generation Pipeline

The explainer agent fits into the broader query generation pipeline:

```
1. User Intent → MetricsQueryIntent
                      ↓
2. Preprocessing → PromQLQuerygenPreprocessor
   - Add aggregation suggestions
   - Transform metric names (Micrometer)
                      ↓
3. LLM Generation → Generate PromQL Query
                      ↓
4. Syntax Validation → PromQLSyntaxValidator
   - Check grammar correctness
                      ↓
5. Schema Validation → MetricsSchemaValidator
   - Verify metric names exist
                      ↓
6. SEMANTIC VALIDATION → PromQLQueryExplainerAgent ← NEW!
   - Verify intent matches generated query
                      ↓
7. Execute Query → PromQL Client
```

## Testing

Unit tests are provided in:
```
tests/unit/codd_engine/validation_engine/agent/metrics/test_promql_query_explainer_agent.py
```

Run tests with:
```bash
pytest tests/unit/codd_engine/validation_engine/agent/metrics/test_promql_query_explainer_agent.py -v
```

## Examples

Complete usage examples are available in:
```
examples/promql_query_explainer_example.py
```

Run examples with:
```bash
python examples/promql_query_explainer_example.py
```

## Dependencies

- `opus-agent-base` - Agent framework with AgentBuilder
- `pydantic-ai>=0.0.30` - AI-native structured outputs
- `openai>=1.0.0` - LLM API client
- `pydantic>=2.0.0` - Data validation

## Configuration

The agent uses the Opus Agent Framework's configuration system:

1. **Config Manager**: Manages LLM settings, API keys, model selection
2. **Instructions Manager**: Loads and manages system prompts
3. **Model Manager**: Handles model selection and fallbacks

Prompts are loaded from:
```
$HOME/.codd/prompts/agent/metrics/PROMQL_QUERY_EXPLAINER_AGENT_INSTRUCTIONS.md
```

## Key Features

✅ **LLM-Powered Semantic Analysis** - Uses AI to understand query intent beyond syntax

✅ **Structured Outputs** - Returns validated Pydantic models with clear results

✅ **Confidence Scoring** - Provides 0.0-1.0 confidence for validation decisions

✅ **Metric Type Awareness** - Understands counter/gauge/histogram/summary semantics

✅ **Detailed Explanations** - Explains both the intent and actual query behavior

✅ **Error Handling** - Robust error handling with clear exception messages

✅ **Comprehensive Testing** - Full unit test coverage with mocked dependencies

## Future Enhancements

Potential improvements:

- [ ] Support for multi-metric queries (unions, joins)
- [ ] Detection of performance anti-patterns (e.g., high cardinality grouping)
- [ ] Suggestions for query optimization
- [ ] Integration with query execution results for runtime validation
- [ ] Support for recording rules and alert expressions
- [ ] Batch validation of multiple queries

## License

Part of the Codd v2 query generation and validation engine.
