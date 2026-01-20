# Codd CLI

Command-line interface for Codd query engine.

## Installation

```bash
# Install in the workspace
uv add codd-cli --workspace

# Or install the package
uv pip install codd-cli
```

## Usage

```bash
# Show help
codd --help

# Get semantic metrics
codd get-semantic-metrics "API high latency" --limit 5

# Construct PromQL query
codd construct-promql-query \
  --description "API error rate" \
  --namespace production \
  --metric-name http_requests_total \
  --aggregation rate \
  --filters '{"status": "500"}'

# Construct LogQL query
codd construct-loki-query \
  --description "Find error logs" \
  --service payments \
  --patterns '[{"pattern": "error", "level": "error"}]'

# Construct Splunk query
codd construct-splunk-query \
  --description "Search for timeouts" \
  --service api-gateway \
  --patterns '[{"pattern": "timeout"}]'
```

## Commands

- `get-semantic-metrics`: Search for relevant metrics using semantic search
- `construct-promql-query`: Generate PromQL queries for Prometheus
- `construct-loki-query`: Generate LogQL queries for Loki
- `construct-splunk-query`: Generate Splunk SPL queries

## Configuration

The CLI uses the Codd configuration from `~/.codd/config.yml` by default.
You can override this with the `--config` option.
