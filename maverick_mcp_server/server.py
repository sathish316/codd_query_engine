#!/usr/bin/env python3
"""Maverick MCP Server - FastMCP-based observability tools server."""

from mcp.server.fastmcp import FastMCP

from maverick_mcp_server.tools import logs, metrics

# Create FastMCP server
mcp = FastMCP("Maverick Observability Server")


# Register metrics tools
@mcp.tool()
async def search_relevant_metrics(problem_json: str, limit: int = 5) -> str:
    """Search for Prometheus metrics relevant to an alert or incident.

    This tool uses semantic search to find metrics that are most relevant to
    your problem description, alert, or incident.

    Args:
        problem_json: JSON string with problem data. Must include 'description' field.
                     Can also include 'keywords', 'category', 'suggested_metrics'.
        limit: Maximum number of metrics to return (default: 5)

    Returns:
        JSON with ranked list of relevant metrics with relevance scores.

    Example:
        Input: {"description": "API experiencing high latency", "category": "performance"}
        Output: {
          "metrics": [
            {"metric_name": "http_request_duration_seconds", "relevance_score": 0.8, ...}
          ]
        }
    """
    return await metrics.search_relevant_metrics(problem_json, limit)


@mcp.tool()
async def construct_promql_query(metrics_query_intent: str) -> str:
    """Generate a valid PromQL query from a metrics query intent.

    Takes a high-level description of what metrics you want to query and generates
    a syntactically correct PromQL query with proper aggregations and filters.

    Args:
        metrics_query_intent: JSON with query intent. Required fields:
            - description: What you want to query
            - namespace: Prometheus namespace
            Optional fields:
            - metric_name: Specific metric to query
            - aggregation: Function like "rate", "sum", "avg"
            - group_by: Labels to group by
            - filters: Label filters as key-value pairs

    Returns:
        JSON with generated PromQL query and metadata.

    Example:
        Input: {
          "description": "API error rate",
          "namespace": "production",
          "metric_name": "http_requests_total",
          "aggregation": "rate",
          "filters": {"status": "500"}
        }
        Output: {
          "query": "rate(http_requests_total{status=\"500\"}[5m])",
          "success": true
        }
    """
    return await metrics.construct_promql_query(metrics_query_intent)


# Register logs tools
@mcp.tool()
async def construct_logql_query(log_query_intent: str) -> str:
    """Generate a valid LogQL query for Loki from a log query intent.

    Creates a syntactically correct LogQL query with proper label selectors,
    line filters, and log pipeline stages.

    Args:
        log_query_intent: JSON with query intent. Required fields:
            - description: What logs to search for
            - backend: Must be "loki"
            - service: Service name
            - patterns: List of patterns like [{"pattern": "error", "level": "error"}]
            Optional fields:
            - default_level: Default log level
            - limit: Max results (default: 200)
            - namespace: Kubernetes namespace

    Returns:
        JSON with generated LogQL query and metadata.

    Example:
        Input: {
          "description": "Find error logs in payments",
          "backend": "loki",
          "service": "payments",
          "patterns": [{"pattern": "error", "level": "error"}]
        }
        Output: {
          "query": "{service=\"payments\"} |~ \"error\" | level=\"error\"",
          "success": true
        }
    """
    return await logs.construct_logql_query(log_query_intent)


@mcp.tool()
async def construct_splunk_query(log_query_intent: str) -> str:
    """Generate a valid Splunk SPL query from a log query intent.

    Creates a syntactically correct Splunk SPL query with proper search terms,
    field filters, and pipe commands.

    Args:
        log_query_intent: JSON with query intent. Required fields:
            - description: What logs to search for
            - backend: Must be "splunk"
            - service: Service name
            - patterns: List of patterns like [{"pattern": "timeout"}]
            Optional fields:
            - default_level: Default log level
            - limit: Max results (default: 200)

    Returns:
        JSON with generated Splunk SPL query and metadata.

    Example:
        Input: {
          "description": "Search for timeout errors",
          "backend": "splunk",
          "service": "api-gateway",
          "patterns": [{"pattern": "timeout"}]
        }
        Output: {
          "query": "search service=\"api-gateway\" \"timeout\" | head 200",
          "success": true
        }
    """
    return await logs.construct_splunk_query(log_query_intent)


def main():
    """Run the MCP server."""
    # Run as stdio server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
