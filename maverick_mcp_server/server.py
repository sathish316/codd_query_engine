#!/usr/bin/env python3
"""Maverick MCP Server - FastMCP-based observability tools server."""

import json
from mcp.server.fastmcp import FastMCP

from maverick_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult,
)
from maverick_mcp_server.client import MaverickClient
from maverick_mcp_server.config import MaverickConfig
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.validation_engine.metrics.structured_outputs import SearchResult

# Create FastMCP server
mcp = FastMCP("Maverick Observability Server")

# Initialize Maverick client (module-level singleton)
_maverick_client: MaverickClient | None = None


def _get_maverick_client() -> MaverickClient:
    """Get or create the Maverick client singleton."""
    global _maverick_client
    if _maverick_client is None:
        config = MaverickConfig()
        _maverick_client = MaverickClient(config=config)
    return _maverick_client


# Register metrics tools
@mcp.tool()
async def search_relevant_metrics(
    problem_json: str, limit: int = 5
) -> list[SearchResult]:
    """Search for Prometheus metrics relevant to an alert or incident.

    This tool uses semantic search to find metrics that are most relevant to
    your problem description, alert, or incident.

    Args:
        problem_json: Search query string
        limit: Maximum number of metrics to return (default: 5)

    Returns:
        List of SearchResult objects with ranked metrics and relevance scores

    Example:
        Input: "API experiencing high latency"
        Output: [
            {
                "metric_name": "http_request_duration_seconds",
                "similarity_score": 0.85,
                "description": "HTTP request duration in seconds",
                ...
            }
        ]
    """
    try:
        # Get client and search
        client = _get_maverick_client()
        results = client.metrics.search_relevant_metrics(problem_json, limit=limit)
        return results

    except Exception:
        # Return empty list on error (matching return type)
        return []


@mcp.tool()
async def construct_promql_query(
    metrics_query_intent: MetricsQueryIntent,
) -> QueryGenerationResult | dict:
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
    try:
        # Parse intent
        intent_data = json.loads(metrics_query_intent)
        intent = MetricsQueryIntent(**intent_data)

        # Get client and generate query
        client = _get_maverick_client()
        result = client.metrics.construct_promql_query(intent)

        return result

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON input: {e}", "query": "", "success": False}
        )
    except Exception as e:
        return json.dumps({"error": str(e), "query": "", "success": False})


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
    try:
        # Parse intent
        intent_data = json.loads(log_query_intent)

        # Ensure backend is loki
        if intent_data.get("backend") != "loki":
            intent_data["backend"] = "loki"

        intent = LogQueryIntent(**intent_data)

        # Get client and generate query
        client = _get_maverick_client()
        result = client.logs.logql.construct_logql_query(intent)

        return json.dumps(
            {
                "query": result.query,
                "backend": "loki",
                "success": result.success,
                "intent": intent_data,
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON input: {e}", "query": "", "success": False}
        )
    except Exception as e:
        return json.dumps(
            {"error": str(e), "query": "", "backend": "loki", "success": False}
        )


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
    try:
        # Parse intent
        intent_data = json.loads(log_query_intent)

        # Ensure backend is splunk
        if intent_data.get("backend") != "splunk":
            intent_data["backend"] = "splunk"

        intent = LogQueryIntent(**intent_data)

        # Get client and generate query
        client = _get_maverick_client()
        result = client.logs.splunk.construct_spl_query(intent)

        return json.dumps(
            {
                "query": result.query,
                "backend": "splunk",
                "success": result.success,
                "intent": intent_data,
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON input: {e}", "query": "", "success": False}
        )
    except Exception as e:
        return json.dumps(
            {"error": str(e), "query": "", "backend": "splunk", "success": False}
        )


def main():
    """Run the MCP server."""
    # Run as stdio server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
