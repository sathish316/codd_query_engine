# Maverick CLI

Command-line interface for Maverick query engine.

## Installation

```bash
# Install in the workspace
uv add maverick-cli --workspace

# Or install the package
uv pip install maverick-cli
```

## Usage

```bash
# Show help
maverick --help

# Get semantic metrics
maverick get-semantic-metrics "API high latency" --limit 5

# Construct PromQL query
maverick construct-promql-query \
  --description "API error rate" \
  --namespace production \
  --metric-name http_requests_total \
  --aggregation rate \
  --filters '{"status": "500"}'

# Construct LogQL query
maverick construct-loki-query \
  --description "Find error logs" \
  --service payments \
  --patterns '[{"pattern": "error", "level": "error"}]'

# Construct Splunk query
maverick construct-splunk-query \
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

The CLI uses the Maverick configuration from `~/.maverick/config.yml` by default.
You can override this with the `--config` option.
