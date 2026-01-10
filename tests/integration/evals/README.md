# Query Generation Evaluation Tests

Property-based integration tests for PromQL, LogQL, and Splunk SPL query generation using static test scenarios.
This can be used as Text2SQL Evalsuite for PromQL, LogQL, Splunk SPL.

## Overview

These tests validate query generation across multiple scenarios using a property-based testing approach. Each scenario tests a specific combination of parameters to ensure comprehensive coverage of query generation capabilities.

## Test Files

- `**test_promql_querygen_evals_integration.py**`
- `**test_logql_querygen_evals_integration.py**`
- `**test_spl_querygen_evals_integration.py**`

## Test Namespace

All tests use the maverick namespace: `**test:text2sql_evals**`

## Running the Tests

### Run All Query Generation Evaluation Tests

```bash
uv run pytest -m integration_querygen_evals -s -v --log-cli-level=INFO
```

### Run Specific Query Language Tests

```bash
# PromQL only
uv run pytest -m integration_querygen_evals tests/integration/evals/test_promql_querygen_evals_integration.py -s -v --log-cli-level=INFO

# LogQL only
uv run pytest -m integration_querygen_evals tests/integration/evals/test_logql_querygen_evals_integration.py -s -v --log-cli-level=INFO

# Splunk SPL only
uv run pytest -m integration_querygen_evals tests/integration/evals/test_spl_querygen_evals_integration.py -s -v --log-cli-level=INFO
```

### List Query Language Scenarios

```bash
# PromQL only
uv run pytest tests/integration/evals/test_promql_querygen_evals_integration.py --collect-only

# LogQL only
uv run pytest tests/integration/evals/test_logql_querygen_evals_integration.py --collect-only

# Splunk SPL only
uv run pytest tests/integration/evals/test_spl_querygen_evals_integration.py --collect-only
```

### Run Specific Scenario

```bash
# Run specific PromQL scenario
uv run pytest -m integration_querygen_evals "tests/integration/evals/test_promql_querygen_evals_integration.py::TestPromQLQueryGenEvalsIntegration::test_promql_query_generation_scenarios[scenario_1_error_logs_single_pattern]" -s -v --log-cli-level=INFO

# Run specific LogQL scenario
uv run pytest -m integration_querygen_evals "tests/integration/evals/test_logql_querygen_evals_integration.py::TestLogQLQueryGenEvalsIntegration::test_logql_query_generation_scenarios[scenario_1_error_logs_single_pattern]" -s -v --log-cli-level=INFO

# Run specific Splunk SPL scenario
uv run pytest -m integration_querygen_evals "tests/integration/evals/test_spl_querygen_evals_integration.py::TestSPLQueryGenEvalsIntegration::test_spl_query_generation_scenarios[scenario_1_error_logs_single_pattern]" -s -v --log-cli-level=INFO
```

### PromQL scenarios - Validated Properties

Each PromQL scenario validates:

- Query generation succeeds
- Generated query contains expected patterns (rate, avg_over_time, etc.)
- Query passes syntax validation
- Metric names are correctly referenced
- Filters and group by clauses are properly formatted

### LogQL scenarios - Validated Properties

Each LogQL scenario validates:

- Query generation succeeds
- Generated query contains expected patterns
- Query has valid LogQL structure (label selectors with braces)
- Service name is correctly referenced
- Log patterns are properly included

### Splunk SPL scenarios - Validated Properties

Each SPL scenario validates:

- Query generation succeeds
- Query starts with 'search' keyword
- Query contains pipe commands
- Query includes result limiting commands (head/limit)
- Service or pattern terms are referenced in query

## Test Structure

Each test uses `@pytest.mark.parametrize` to iterate over static scenarios:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", PROMQL_TEST_SCENARIOS, ids=lambda s: s["id"])
async def test_promql_query_generation_scenarios(self, scenario, query_generator, metadata_store):
    # Test implementation
    pass
```

## Scenario Structure

Each scenario is a dictionary with:

```python
{
    "id": "scenario_1_counter_with_rate",
    "description": "Human-readable description",
    "intent": MetricsQueryIntent(...),  # or LogQueryIntent
    "expected_patterns": ["rate(", "http_requests_total", ...],
    "metrics_to_seed": ["http_requests_total", ...]  # For PromQL only
}
```

## Adding New Scenarios

To add a new scenario:

1. Add a new dictionary to the `*_TEST_SCENARIOS` array
2. Provide a unique `id`
3. Define the `intent` with appropriate parameters
4. List `expected_patterns` to validate in the generated query
5. For PromQL, specify `metrics_to_seed` for the metadata store

Example:

```python
{
    "id": "scenario_8_custom_test",
    "description": "My custom test scenario",
    "intent": MetricsQueryIntent(
        metric="custom_metric",
        metric_type="counter",
        filters={"label": "value"},
        window="5m",
        aggregation_suggestions=[
            AggregationFunctionSuggestion(function_name="rate")
        ],
    ),
    "expected_patterns": ["rate(", "custom_metric", "5m"],
    "metrics_to_seed": ["custom_metric"],
}
```

## Test Output

Each test outputs:

- Scenario ID and description
- Intent being tested
- Generated query
- Validation results
- Expected patterns found

Example output:

```
================================================================================
Testing Scenario: scenario_1_counter_with_rate
Description: Counter metric with rate aggregation and filters
Intent: Calculate rate of HTTP 500 errors per second over 5 minutes
================================================================================
✓ Scenario scenario_1_counter_with_rate passed
  Generated query: rate(http_requests_total{status="500",method="POST"}[5m]) by (instance, job)
  All expected patterns found: ['rate(', 'http_requests_total', 'status="500"', '5m', 'by (']
```

