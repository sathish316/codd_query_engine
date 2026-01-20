# Codd MCP Server - Cursor Usage Guide

AI-powered observability tools accessible via MCP (Model Context Protocol) in Cursor and other MCP clients.

## Overview

The Codd MCP Server provides four powerful tools for observability:

### Metrics Tools
1. **`search_relevant_metrics`** - Find Prometheus or other TSDB metrics relevant to your problem
2. **`construct_promql_query`** - Generate valid PromQL queries from intent

### Logs Tools
3. **`construct_logql_query`** - Generate valid LogQL queries for Loki
4. **`construct_splunk_query`** - Generate valid Splunk SPL queries

## Installation

### 1. Install Dependencies

```bash
cd /path/to/codd_query_engine
uv sync
```

### 2. Configure Cursor

Add the Codd MCP server to your Cursor MCP settings:

**mcp.json**
```json
{
  "mcpServers": {
    "codd": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/codd_query_engine",
        "python",
        "-m",
        "codd_mcp_server.server"
      ],
      "env": {
        "PYTHONPATH": "/path/to/codd_query_engine"
      }
    }
  }
}
```

### 3. Restart Cursor

After updating the configuration, restart Cursor to load the MCP server.

### 4. Verify Installation

In Cursor, you should see the Codd tools available. You can verify by:
1. Opening Cursor Settings → MCP
2. Checking that "codd" server is listed and connected
3. Looking for the 4 Codd tools in the available tools list

## Tool Usage Examples

### Tool 1: `search_relevant_metrics`

**Purpose:** Find Prometheus metrics relevant to an alert, incident, or problem description.

#### Example 1: Search for API Latency Metrics

```
Use search_relevant_metrics to find metrics related to this problem:

{
  "description": "API experiencing high latency on the payments endpoint",
  "category": "performance",
  "keywords": ["latency", "api", "payments", "slow"]
}
```

---

### Tool 2: `construct_promql_query`

**Purpose:** Generate a syntactically correct PromQL query from a high-level intent.

#### Example 1: Basic Error Rate Query

```
Use construct_promql_query to generate a PromQL query for:

{
  "description": "Calculate the error rate for the API service over the last 5 minutes",
  "namespace": "production",
  "metric_name": "http_requests_total",
  "aggregation": "rate",
  "filters": {
    "status": "500",
    "service": "payment-service"
  }
}
```

#### Example 3: Two-Step Workflow

```
1. First, search for metrics related to "CPU usage"
2. Take the top metric from search results
3. Use `construct_promql_query` to create a query that shows CPU usage by instance grouped over 1 minute

For step 3, use:
{
  "description": "CPU usage per instance",
  "namespace": "production",
  "metric_name": "<top_metric_from_search>",
  "aggregation": "avg",
  "group_by": ["instance"]
}
```

### Tool 3: `construct_logql_query`

**Purpose:** Generate a valid LogQL query for Loki log aggregation.

#### Example 1: Find Error Logs

```
Use construct_logql_query to find error logs in payment-service:

{
  "description": "Find all error-level logs in the payments service",
  "backend": "loki",
  "service": "payment-service",
  "patterns": [
    {"pattern": "error", "level": "error"}
  ],
  "limit": 100
}
```

#### Example 2: Kubernetes Logs

```
Find error logs from specific pods:

{
  "description": "Errors from checkout pods in production namespace",
  "backend": "loki",
  "namespace": "production",
  "patterns": [
    {"pattern": "exception|error|fail", "level": "error"}
  ],
  "limit": 50
}
```

#### Example 3: From Alert to Logs

```
Given this alert:
"Database connection timeouts in payment processing"

1. Extract key patterns (timeout, database, connection)
2. Use construct_logql_query with:

{
  "description": "Database connection timeout logs",
  "backend": "loki",
  "service": "payment-processor",
  "patterns": [
    {"pattern": "timeout"},
    {"pattern": "database"},
    {"pattern": "connection"}
  ]
}
```

---

### Tool 4: `construct_splunk_query`

**Purpose:** Generate a valid Splunk SPL query.

#### Example 1: Basic Error Search

```
Use construct_splunk_query to search for errors in payment-service:

{
  "description": "Find error logs in the payment-service",
  "backend": "splunk",
  "service": "payment-service",
  "patterns": [
    {"pattern": "error", "level": "error"}
  ],
  "limit": 100
}
```

#### Example 2: Status Code Filtering

```
Generate Splunk query for HTTP 5xx errors:

{
  "description": "Search for all 500-level HTTP errors",
  "backend": "splunk",
  "service": "api-gateway",
  "patterns": [
    {"pattern": "status=500"}
  ],
  "limit": 200
}
```

#### Example 3: Time-Based Search

```
Generate Splunk query for HTTP 5xx errors in last one hour:

{
  "description": "Search for all 500-level HTTP errors",
  "backend": "splunk",
  "service": "api-gateway",
  "patterns": [
    {"pattern": "status=500"}
  ],
  "limit": 200
}
```

---

## Complete Workflows

### Workflow 1: Alert → Metrics → Query

```
I have an alert: "API latency increased by 200% in the last 10 minutes"

Please:
1. Use search_relevant_metrics to find relevant metrics
2. Take the top 3 metrics
3. For each metric, use construct_promql_query to create a query showing the rate over 5 minutes
```

**Steps Cursor will execute:**
1. `search_relevant_metrics` with alert data
2. Get top 3: `http_request_duration_seconds`, `api_latency_ms`, `request_processing_time`
3. Three calls to `construct_promql_query` for each metric

### Workflow 2: Incident Investigation

```
Investigating incident: "Payments service experiencing intermittent 500 errors"

Help me:
1. Find relevant metrics using search_relevant_metrics
2. Generate a PromQL query for error rate
3. Generate both LogQL and Splunk queries to search error logs
```

**Tool Calls:**
1. `search_relevant_metrics` → finds payment error metrics
2. `construct_promql_query` → generates error rate query
3. `construct_logql_query` → generates Loki query for errors
4. `construct_splunk_query` → generates Splunk SPL query for errors

### Workflow 3: Performance Analysis

```
Analyze performance issue: "Database queries slowing down"

1. Search for database-related metrics
2. Create PromQL queries for:
   - Query duration (p95, p99)
   - Active connections
   - Query throughput
3. Generate log queries to find slow query logs
```

### Workflow 4: Service Health Dashboard

```
Create queries for a service health dashboard for the "checkout" service:

1. Find all relevant metrics for the checkout service
2. Generate PromQL queries for:
   - Request rate (QPS)
   - Error rate
   - Latency (p50, p95, p99)
   - Resource usage (CPU, Memory)
3. Create log queries for errors and warnings
```

---

## Troubleshooting


