# Codd Lib

Reusable client library for observability operations (metrics and logs).

## Features

- **Metrics Operations**: Semantic search and PromQL query generation
- **Logs Operations**: LogQL and Splunk SPL query generation
- **Provider Pattern**: Spring-like dependency injection for clean architecture
- **Configurable**: Pydantic-based configuration with sensible defaults

## Installation

```bash
# As workspace dependency
uv add codd-lib --workspace
```

## Usage

### Basic Usage

```python
from codd_lib import CoddClient, CoddConfig

# Initialize with default config
config = CoddConfig()
client = CoddClient(config)

# Search for relevant metrics
results = client.metrics.search_relevant_metrics("API high latency", limit=5)

# Generate PromQL query
from codd_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent

intent = MetricsQueryIntent(
    description="API error rate",
    namespace="production",
    metric_name="http_requests_total",
    aggregation="rate",
    filters={"status": "500"}
)
result = client.metrics.construct_promql_query(intent)
print(result.query)  # rate(http_requests_total{status="500"}[5m])
```

### Custom Configuration

```python
from codd_lib.config import (
    CoddConfig,
    PrometheusConfig,
    RedisConfig,
    SemanticStoreConfig,
)

config = CoddConfig(
    prometheus=PrometheusConfig(
        base_url="https://prometheus.example.com",
        auth_token="secret-token"
    ),
    redis=RedisConfig(
        host="redis.example.com",
        port=6380,
        db=1
    ),
    semantic_store=SemanticStoreConfig(
        chromadb_host="chromadb.example.com",
        chromadb_port=8001
    )
)

client = CoddClient(config)
```

### Using Individual Clients

```python
from codd_lib import MetricsPromQLClient, CoddConfig
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

config = CoddConfig()
config_manager = ConfigManager("/path/to/config", "config.yml")
instructions_manager = InstructionsManager()

# Use metrics client directly
metrics_client = MetricsPromQLClient(config, config_manager, instructions_manager)
results = metrics_client.search_relevant_metrics("query", limit=5)
```

## Architecture

- **Client Layer**: High-level clients composing domain operations
  - `CoddClient`: Main orchestrator
  - `MetricsClient`: Metrics operations (delegates to PromQL client)
  - `LogsClient`: Logs operations (delegates to LogQL/Splunk clients)

- **Provider Layer**: Dependency injection modules
  - `PromQLModule`: PromQL dependencies (stores, validators, generators)
  - `LogQLModule`: LogQL dependencies
  - `SplunkModule`: Splunk dependencies
  - `OpusModule`: Opus Agent dependencies

- **Config Layer**: Pydantic configuration models
  - `CoddConfig`: Main config orchestrator
  - Backend-specific configs (Prometheus, Loki, Splunk, Redis, etc.)

## Testing

```bash
# Run unit tests
pytest tests/unit

# Run integration tests
pytest tests/integration -m integration

# Run all tests
pytest tests
```

## Dependencies

- `codd-engine`: Query generation and validation engine
- `codd-dal`: Data access layer
- `opus-agent-base`: LLM agent framework
- `chromadb`: Vector store for semantic search
- `redis`: Metrics metadata store
- `pydantic`: Configuration validation
