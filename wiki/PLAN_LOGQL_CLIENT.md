# LogQL Client for Log Patterns Metadata and Query Execution

This module provides a complete LogQL client implementation for Grafana Loki, including metadata management and query execution capabilities.

## Components

### 1. LogsMetadataClient (Redis-based)
**File**: `logs_metadata_client.py`

Redis-based store for log patterns metadata, optimized for fast validation.

**Features**:
- Store and validate stream label names
- Store and validate label values
- Namespace isolation for multi-tenancy
- Fast exact-match lookups

**Key Methods**:
```python
# Stream labels management
set_stream_labels(namespace, label_names)
get_stream_labels(namespace)
add_stream_label(namespace, label_name)
is_valid_stream_label(namespace, label_name)

# Label values management
set_label_values(namespace, label_name, values)
get_label_values(namespace, label_name)
add_label_value(namespace, label_name, value)
is_valid_label_value(namespace, label_name, value)
```

**Usage Example**:
```python
import redis
from maverick_dal.logs import LogsMetadataClient

# Initialize
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
client = LogsMetadataClient(redis_client)

# Add stream labels
client.add_stream_label("production", "job")
client.add_stream_label("production", "level")

# Add label values
client.add_label_value("production", "job", "api")
client.add_label_value("production", "job", "frontend")
client.add_label_value("production", "level", "error")

# Validate
assert client.is_valid_stream_label("production", "job") == True
assert client.is_valid_label_value("production", "job", "api") == True
```

### 2. LogsSemanticMetadataStore (ChromaDB-based)
**File**: `logs_semantic_metadata_store.py`

Vector-based semantic search for log patterns using ChromaDB embeddings.

**Features**:
- Semantic search for log patterns by natural language
- Rich metadata storage (description, source, severity, category)
- Similarity scoring for search results
- Input validation and sanitization

**Key Methods**:
```python
index_metadata(namespace, metadata)  # Index log pattern metadata
search_metadata(namespace, query, n_results)  # Semantic search
```

**Usage Example**:
```python
import chromadb
from maverick_dal.logs import LogsSemanticMetadataStore, LogPatternMetadata

# Initialize
chroma_client = chromadb.Client()
store = LogsSemanticMetadataStore(chroma_client)

# Index log pattern
metadata: LogPatternMetadata = {
    "pattern_name": "authentication_failure",
    "description": "Failed login attempts from unauthorized users",
    "source": "auth-service",
    "severity": "error",
    "category": "security",
    "subcategory": "authentication",
    "labels": '{"job": "auth", "level": "error"}'
}
store.index_metadata("production", metadata)

# Search
results = store.search_metadata("production", "security incidents", n_results=10)
```

### 3. LogQLQueryExecutor
**File**: `logql_query_executor.py`

Direct query execution against Grafana Loki using the HTTP API.

**Features**:
- Range queries (time-series data)
- Instant queries (point-in-time)
- Label metadata retrieval
- Authentication support (Bearer token, Org ID)
- Context manager support

**Key Methods**:
```python
query_range(query, start, end, limit, direction, step)
query_instant(query, time, limit, direction)
get_labels(start, end)
get_label_values(label_name, start, end, query)
```

**Usage Example**:
```python
from datetime import datetime, timedelta
from maverick_dal.logs import LogQLQueryExecutor, LokiConfig

# Configure
config = LokiConfig(
    base_url="http://localhost:3100",
    auth_token="your-token",  # Optional
    org_id="your-org"  # Optional
)

# Execute queries
with LogQLQueryExecutor(config) as executor:
    # Range query
    result = executor.query_range(
        query='{job="api", level="error"}',
        start=datetime.now() - timedelta(hours=1),
        end=datetime.now(),
        limit=100
    )

    if result.status == "success":
        print(result.data)

    # Get available labels
    labels = executor.get_labels()

    # Get label values
    job_values = executor.get_label_values("job")
```

### 4. LogQL Expression Parser
**Files**:
- `validation_engine/logql/logql_expression_parser.py` (Protocol)
- `validation_engine/logql/pydantic_logql_parser.py` (LLM-based implementation)
- `validation_engine/logql/logql_structured_outputs.py` (Pydantic models)

LLM-based parser for extracting stream selectors from LogQL expressions.

**Features**:
- Extracts label matchers from LogQL queries
- Confidence scoring for extractions
- Validation of label name format
- Handles complex LogQL syntax (pipelines, aggregations)

**Usage Example**:
```python
from maverick_engine.config.llm_settings import LLMSettings
from maverick_engine.validation_engine.logql import PydanticAILogQLExpressionParser

# Initialize
settings = LLMSettings(
    api_key="your-openai-key",
    model_name="gpt-4",
    confidence_threshold=0.8
)
parser = PydanticAILogQLExpressionParser(settings)

# Parse LogQL expression
selectors = parser.parse('{job="api", level="error"} |= "timeout"')
# Returns: {"job": {"api"}, "level": {"error"}}

# Complex query
selectors = parser.parse('rate({namespace="production", app=~"web-.*"}[5m])')
# Returns: {"namespace": {"production"}, "app": {"web-.*"}}
```

## Architecture

The implementation follows the existing Maverick patterns:

1. **Data Access Layer** (`maverick_dal/logs/`):
   - Redis metadata store (exact matching)
   - ChromaDB semantic store (similarity search)
   - Loki HTTP client (query execution)

2. **Validation Engine** (`maverick_engine/validation_engine/logql/`):
   - Protocol-based parser interface
   - PydanticAI implementation for LLM parsing
   - Structured output models

3. **Testing** (`maverick_dal/logs/tests/`):
   - Comprehensive unit tests
   - FakeRedis for metadata testing
   - Mock HTTP client for query executor testing

## Dependencies

Added to `maverick_dal/pyproject.toml`:
```toml
dependencies = [
    "redis>=5.0.0",
    "fakeredis>=2.0.0",
    "chromadb>=0.4.0",
    "httpx>=0.25.0",
]
```

## Testing

Run tests from the project root:
```bash
# Run all logs tests
uv run pytest maverick_dal/logs/tests/ -v

# Run specific test file
uv run pytest maverick_dal/logs/tests/test_logs_metadata_client.py -v
uv run pytest maverick_dal/logs/tests/test_logql_query_executor.py -v
```

## Integration with Validation Pipeline

The LogQL components can be integrated into a validation pipeline similar to the metrics validation:

1. Parse LogQL expression using `PydanticAILogQLExpressionParser`
2. Validate stream labels using `LogsMetadataClient.is_valid_stream_label()`
3. Validate label values using `LogsMetadataClient.is_valid_label_value()`
4. Execute validated query using `LogQLQueryExecutor`

## Next Steps

To complete the LogQL implementation:

1. **Create LogQL Schema Validator** (similar to `metric_expression_parser.py`):
   - Orchestrate parser and metadata validation
   - Return structured validation results

2. **Add Service Layer Endpoints**:
   - REST API for log pattern management
   - Query execution endpoints
   - Label metadata endpoints

3. **Implement Semantic Preprocessing**:
   - Use semantic store for query suggestions
   - Pattern recommendation based on user queries

4. **Create Documentation**:
   - API documentation
   - Usage examples
   - Integration guides

5. **Add Demo/Evaluation Suite**:
   - Example log patterns
   - Common query patterns
   - NL2LogQL evaluation

## Reference Implementation

This implementation mirrors the metrics system:
- `metrics_metadata_client.py` → `logs_metadata_client.py`
- `metrics_semantic_metadata_store.py` → `logs_semantic_metadata_store.py`
- `pydantic_metric_parser.py` → `pydantic_logql_parser.py`

All patterns, error handling, and testing approaches follow the established codebase conventions.
