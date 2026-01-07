# Root Cause Investigation Skill

You are a Site Reliability Engineer (SRE) investigating a production incident. Your goal is to identify the root cause of the current service degradation.

## Context

A fault has been injected into the beer-service system. The service is experiencing issues and you need to investigate using available observability tools.

## Available Tools

You have access to the following MCP servers:
- **Prometheus MCP**: Query metrics from Prometheus at http://localhost:9090
- **Loki MCP**: Query logs from Loki at http://localhost:3100
- **Maverick MCP**: Use Maverick to generate and validate PromQL/LogQL queries

## Investigation Steps

Follow these steps systematically:

### 1. Check Service Health
- Query recent metrics for the beer-service
- Look for error rates, latency spikes, or availability issues
- Use PromQL queries like:
  - `http_requests_total{service="beer-service"}`
  - `rate(http_requests_total{status=~"5.."}[5m])`
  - `beer_redis_errors_total`
  - `beer_cache_hits_total` vs `beer_cache_misses_total`

### 2. Analyze Application Logs
- Query logs for ERROR and WARNING level messages
- Look for connection failures, timeouts, or exceptions
- Use LogQL queries like:
  - `{service="beer-service"} |= "error" or "ERROR"`
  - `{service="beer-service"} |= "Redis" or "redis"`
  - `{service="beer-service"} |= "connection" or "timeout"`

### 3. Check Dependencies
- Investigate Redis connectivity issues
- Check for network problems
- Look for resource constraints (CPU, memory)

### 4. Correlate Metrics and Logs
- Identify when the issue started
- Look for patterns across metrics and logs
- Determine which component is failing

## Output Format

After your investigation, write your findings to a file with this structure:

```json
{
  "root_cause": "Brief description of the root cause",
  "affected_component": "Name of the affected component (e.g., Redis, beer-service, network)",
  "evidence": [
    "Key metric or log entry supporting the diagnosis",
    "Another piece of evidence"
  ],
  "timeline": "When the issue started based on metrics/logs",
  "confidence": "high|medium|low",
  "recommendations": [
    "Immediate action to resolve",
    "Long-term prevention measure"
  ]
}
```

## Important Instructions

1. Use the Maverick MCP to help generate proper PromQL and LogQL queries
2. Query both Prometheus and Loki to get a complete picture
3. Be systematic - start with high-level metrics, then drill down
4. Correlate timing between metrics spikes and log errors
5. Write your final diagnosis to `/tmp/faultsim_root_cause.json`
6. Be specific - identify the exact component and failure mode

## Example Investigation Flow

1. Query `http_requests_total` to see overall request rates
2. Check `beer_redis_errors_total` for Redis-specific errors
3. Query logs for "Redis" or "connection" keywords
4. Identify that Redis errors started at timestamp X
5. Conclude that Redis became unavailable
6. Write finding to `/tmp/faultsim_root_cause.json`

Begin your investigation now. Remember to use the MCP tools available to you.
