#!/usr/bin/env python3
"""Maverick MCP Server - FastMCP-based observability tools server."""

import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from maverick_lib.models import MetricsQueryIntent, LogQueryIntent

# Create FastMCP server
mcp = FastMCP("Maverick Observability Server")

# Maverick service base URL (configurable via environment variable)
MAVERICK_SERVICE_URL = os.getenv("MAVERICK_SERVICE_URL", "http://localhost:2840")


def _make_request(
    endpoint: str, method: str = "POST", json_data: dict | None = None
) -> dict[str, Any]:
    """Make HTTP request to Maverick service.

    Args:
        endpoint: API endpoint path (e.g., "/api/metrics/search")
        method: HTTP method (default: POST)
        json_data: JSON payload for request

    Returns:
        Response JSON as dictionary

    Raises:
        httpx.HTTPError: If request fails
    """
    url = f"{MAVERICK_SERVICE_URL}{endpoint}"

    with httpx.Client(timeout=120.0) as client:
        if method == "POST":
            response = client.post(url, json=json_data)
        elif method == "GET":
            response = client.get(url, params=json_data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()


# Register metrics tools
@mcp.tool()
async def search_relevant_metrics(
    problem_json: str, limit: int = 5
) -> list[dict[str, Any]]:
    """Search for Prometheus metrics relevant to an alert or incident.

    This tool uses semantic search to find metrics that are most relevant to
    your problem description, alert, or incident.

    Args:
        problem_json: Search query string
        limit: Maximum number of metrics to return (default: 5)

    Returns:
        List of metric results with ranked metrics and relevance scores

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
        # Make request to metrics search endpoint
        response = _make_request(
            endpoint="/api/metrics/search",
            method="POST",
            json_data={"query": problem_json, "limit": limit},
        )

        return response.get("results", [])

    except Exception as e:
        # Return empty list on error
        print(f"Error searching metrics: {e}")
        return []


@mcp.tool()
async def construct_promql_query(
    intent: MetricsQueryIntent,
) -> dict[str, Any]:
    """Generate a valid PromQL query from a metrics query intent.

    Takes a high-level description of what metrics you want to query and generates
    a syntactically correct PromQL query with proper aggregations and filters.

    Args:
        intent: Metrics query intent with the following fields:
            - description (required): What you want to query
            - namespace (required): Maverick Text2SQL namespace
            - metric_name (required): Specific metric to query
            - service (required): Service name to filter metrics
            - meter_type: Type of meter (counter, gauge, histogram, summary)
            - aggregation: Function like "rate", "sum", "avg"
            - group_by: Labels to group by
            - filters: Label filters as key-value pairs
            - window: Time range window (e.g., "1m", "5m", "1h"). Default: "5m"
            - query_opts: Query generation options

    Returns:
        Dict with generated PromQL query and metadata.

    Example:
        Input: MetricsQueryIntent(
          description="API error rate",
          namespace="production",
          metric_name="http_requests_total",
          service="api-gateway",
          aggregation="rate",
          filters={"status": "500"},
          window="1m"
        )
        Output: {
          "query": "rate(http_requests_total{status=\"500\"}[1m])",
          "success": true
        }
    """
    try:
        # Make request to PromQL generation endpoint
        response = _make_request(
            endpoint="/api/metrics/promql/generate",
            method="POST",
            json_data=intent.model_dump(exclude_none=True),
        )

        return response

    except Exception as e:
        return {"error": str(e), "query": "", "success": False}


# Register logs tools
@mcp.tool()
async def construct_logql_query(intent: LogQueryIntent) -> dict[str, Any]:
    """Generate a valid LogQL query for Loki from a log query intent.

    Creates a syntactically correct LogQL query with proper label selectors,
    line filters, and log pipeline stages.

    Args:
        intent: Log query intent with the following fields:
            - description (required): What logs to search for
            - service (required): Service name
            - patterns (required): List of patterns like [{"pattern": "error", "level": "error"}]
            - namespace (required): Maverick Text2SQL namespace
            - default_level: Default log level
            - limit: Max results (default: 200)

    Returns:
        Dict with generated LogQL query and metadata.

    Example:
        Input: LogQueryIntent(
          description="Find error logs in payments",
          service="payments",
          namespace="production",
          patterns=[LogPattern(pattern="error", level="error")]
        )
        Output: {
          "query": "{service=\"payments\"} |~ \"error\" | level=\"error\"",
          "success": true
        }
    """
    try:
        # Make request to LogQL generation endpoint
        response = _make_request(
            endpoint="/api/logs/logql/generate",
            method="POST",
            json_data=intent.model_dump(exclude_none=True),
        )

        return {
            "query": response.get("query", ""),
            "backend": response.get("backend", "loki"),
            "success": response.get("success", False),
            "error": response.get("error"),
        }

    except Exception as e:
        return {"error": str(e), "query": "", "backend": "loki", "success": False}


@mcp.tool()
async def construct_splunk_query(intent: LogQueryIntent) -> dict[str, Any]:
    """Generate a valid Splunk SPL query from a log query intent.

    Creates a syntactically correct Splunk SPL query with proper search terms,
    field filters, and pipe commands.

    Args:
        intent: Log query intent with the following fields:
            - description (required): What logs to search for
            - service (required): Service name
            - patterns (required): List of patterns like [{"pattern": "timeout"}]
            - namespace (required): Maverick Text2SQL namespace
            - default_level: Default log level
            - limit: Max results (default: 200)

    Returns:
        Dict with generated Splunk SPL query and metadata.

    Example:
        Input: LogQueryIntent(
          description="Search for timeout errors",
          service="api-gateway",
          namespace="production",
          patterns=[LogPattern(pattern="timeout")]
        )
        Output: {
          "query": "search service=\"api-gateway\" \"timeout\" | head 200",
          "success": true
        }
    """
    try:
        # Make request to Splunk generation endpoint
        response = _make_request(
            endpoint="/api/logs/splunk/generate",
            method="POST",
            json_data=intent.model_dump(exclude_none=True),
        )

        return {
            "query": response.get("query", ""),
            "backend": response.get("backend", "splunk"),
            "success": response.get("success", False),
            "error": response.get("error"),
        }

    except Exception as e:
        return {"error": str(e), "query": "", "backend": "splunk", "success": False}


def main():
    """Run the MCP server."""
    # Run as stdio server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
