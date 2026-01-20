# PromQL Client

A Python client for querying Prometheus using PromQL. Supports metadata queries and query execution (instant and range queries).

## Features

### Metadata Queries
- Get label names
- Get label values for specific labels
- Get time series matching selectors
- Get metric metadata (type, help, unit)

### Query Execution
- Instant queries (single point in time)
- Range queries (over a time range)
- Custom timeout support
- Time filtering for metadata queries

### Utilities
- Health checks
- Readiness checks
- Context manager support for automatic cleanup

## Installation

The client requires `httpx` for HTTP requests:

```bash
uv add httpx
```

## Usage

### Basic Initialization

```python
from codd_dal.metrics.promql_client import PromQLClient

# Basic initialization
client = PromQLClient("http://localhost:9090")

# With custom timeout
client = PromQLClient("http://localhost:9090", timeout=60.0)

# With authentication
client = PromQLClient(
    "http://localhost:9090",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Context Manager

```python
with PromQLClient("http://localhost:9090") as client:
    result = client.query_instant("up")
    # Client automatically closes when exiting
```

### Metadata Queries

#### Get Label Names

```python
# Get all label names
labels = client.get_label_names()

# Get labels for specific time range
from datetime import datetime, timedelta
end = datetime.now()
start = end - timedelta(days=1)
labels = client.get_label_names(start=start, end=end)

# Get labels matching specific series
labels = client.get_label_names(match=["up", "node_cpu_seconds_total"])
```

#### Get Label Values

```python
# Get all values for a label
jobs = client.get_label_values("job")

# Get label values with time filter
instances = client.get_label_values(
    "instance",
    start=start,
    end=end,
    match=["up"]
)
```

#### Get Series

```python
# Get series matching selectors
series = client.get_series(match=["up"])

# Get series for time range
series = client.get_series(
    match=["up", "node_cpu_seconds_total"],
    start=start,
    end=end
)
```

#### Get Metric Metadata

```python
# Get metadata for all metrics
metadata = client.get_metric_metadata()

# Get metadata for specific metric
metadata = client.get_metric_metadata(metric="up")

# Limit results
metadata = client.get_metric_metadata(metric="up", limit=10)
```

### Query Execution

#### Instant Query

```python
# Query at current time
result = client.query_instant("up")

# Query at specific time
from datetime import datetime
query_time = datetime(2024, 1, 1, 12, 0, 0)
result = client.query_instant("up", time=query_time)

# Query with timeout
result = client.query_instant("up", timeout="30s")

# Complex queries
result = client.query_instant("sum by (job) (rate(http_requests_total[5m]))")
```

#### Range Query

```python
from datetime import datetime, timedelta

# Query over time range
end = datetime.now()
start = end - timedelta(hours=1)

result = client.query_range(
    query="rate(http_requests_total[5m])",
    start=start,
    end=end,
    step="1m"
)

# Query with timeout
result = client.query_range(
    query="up",
    start=start,
    end=end,
    step="30s",
    timeout="60s"
)
```

### Health Checks

```python
# Check if Prometheus is healthy
is_healthy = client.health_check()

# Check if Prometheus is ready
is_ready = client.ready_check()
```

## Response Formats

### Instant Query Response

```python
{
    "resultType": "vector",  # or "scalar", "matrix", "string"
    "result": [
        {
            "metric": {
                "__name__": "up",
                "job": "prometheus",
                "instance": "localhost:9090"
            },
            "value": [1704067200, "1"]  # [timestamp, value]
        }
    ]
}
```

### Range Query Response

```python
{
    "resultType": "matrix",
    "result": [
        {
            "metric": {
                "__name__": "up",
                "job": "prometheus"
            },
            "values": [
                [1704067200, "1"],  # [timestamp, value]
                [1704067260, "1"],
                [1704067320, "1"]
            ]
        }
    ]
}
```

### Series Response

```python
[
    {
        "__name__": "up",
        "job": "prometheus",
        "instance": "localhost:9090"
    },
    {
        "__name__": "up",
        "job": "node",
        "instance": "localhost:9100"
    }
]
```

### Metadata Response

```python
{
    "up": [
        {
            "type": "gauge",
            "help": "1 if the instance is up, 0 otherwise",
            "unit": ""
        }
    ]
}
```

## Error Handling

```python
import httpx

try:
    result = client.query_instant("up")
except ValueError as e:
    # Prometheus API errors (invalid query, etc.)
    print(f"API error: {e}")
except httpx.HTTPError as e:
    # HTTP/network errors
    print(f"HTTP error: {e}")
```

## Common Query Examples

### CPU Usage

```python
# CPU usage per instance
query = 'sum by (instance) (rate(node_cpu_seconds_total[5m]))'
result = client.query_instant(query)
```

### Memory Usage

```python
# Memory usage percentage
query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
result = client.query_instant(query)
```

### HTTP Request Rate

```python
# Request rate per endpoint
query = 'sum by (endpoint) (rate(http_requests_total[5m]))'
result = client.query_instant(query)
```

### Top K Queries

```python
# Top 5 instances by CPU
query = 'topk(5, sum by (instance) (rate(node_cpu_seconds_total[5m])))'
result = client.query_instant(query)
```

### Aggregations

```python
# Average response time
query = 'avg(http_request_duration_seconds)'
result = client.query_instant(query)

# Total requests
query = 'sum(http_requests_total)'
result = client.query_instant(query)

# P95 response time
query = 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
result = client.query_instant(query)
```

## Testing

The client includes comprehensive tests using pytest and mocked HTTP responses:

```bash
pytest codd_dal/metrics/tests/test_promql_client.py -v
```

### Test Coverage

- Initialization and configuration
- Context manager protocol
- Metadata queries (labels, values, series)
- Query execution (instant and range)
- Error handling (API errors, HTTP errors, network errors)
- Utility methods (health and readiness checks)

## API Reference

### Constructor

```python
PromQLClient(
    base_url: str,
    timeout: float = 30.0,
    headers: Optional[dict[str, str]] = None
)
```

### Metadata Methods

- `get_label_names(start=None, end=None, match=None) -> list[str]`
- `get_label_values(label_name, start=None, end=None, match=None) -> list[str]`
- `get_series(match, start=None, end=None) -> list[dict[str, str]]`
- `get_metric_metadata(metric=None, limit=None) -> dict[str, list[dict[str, str]]]`

### Query Methods

- `query_instant(query, time=None, timeout=None) -> dict[str, Any]`
- `query_range(query, start, end, step, timeout=None) -> dict[str, Any]`

### Utility Methods

- `health_check() -> bool`
- `ready_check() -> bool`
- `close()` - Close HTTP client

## Notes

- All datetime parameters should be `datetime` objects
- Step parameter for range queries uses Prometheus duration format: "15s", "1m", "1h", etc.
- Timeout parameter uses Prometheus duration format: "30s", "1m", etc.
- The client uses `httpx` for HTTP requests with connection pooling
- Context manager automatically closes the HTTP client

## Related Files

- Implementation: `codd_dal/metrics/promql_client.py`
- Tests: `codd_dal/metrics/tests/test_promql_client.py`
- Example: `codd_dal/metrics/examples/promql_client_example.py`
