"""Metrics-related MCP tools."""

import json
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_mcp_server.client import MetricsClient
from maverick_mcp_server.config import MaverickConfig

# Initialize the metrics client once (module-level singleton)
_metrics_client = None


def _get_metrics_client() -> MetricsClient:
    """Get or create the metrics client singleton."""
    global _metrics_client
    if _metrics_client is None:
        # Use default config (can be customized via environment variables later)
        config = MaverickConfig()
        _metrics_client = MetricsClient(config=config)
    return _metrics_client


async def search_relevant_metrics(problem_json: str, limit: int = 5) -> str:
    """Search for metrics relevant to a problem - alert or incident.

    Uses semantic search to find metrics similar to the problem description.

    Args:
        problem_json: JSON string containing problem data with at least a 'description' field.
                     Can include 'keywords', 'category', etc.
        limit: Maximum number of metrics to return (default: 5)

    Returns:
        JSON string with relevant metrics ranked by similarity score.

    Example input:
        {
          "description": "API experiencing high latency",
          "category": "performance",
          "keywords": ["latency", "api", "slow"]
        }

    Example output:
        {
          "query": "API experiencing high latency",
          "metrics": [
            {
              "metric_name": "http_request_duration_seconds",
              "similarity_score": 0.85,
              "description": "HTTP request duration",
              ...
            }
          ]
        }
    """
    try:
        # Parse input
        problem_data = json.loads(problem_json)

        # Extract description for semantic search
        description = problem_data.get("description", "")
        if not description:
            return json.dumps({"error": "description field is required", "metrics": []})

        # Get client and search
        client = _get_metrics_client()
        results = client.search_relevant_metrics(description, limit=limit)

        return json.dumps(
            {
                "query": description,
                "metrics": results,
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON input: {e}", "metrics": []})
    except Exception as e:
        return json.dumps({"error": f"Error searching metrics: {e}", "metrics": []})


async def construct_promql_query(metrics_query_intent: str) -> str:
    """Generate a valid PromQL query from metrics query intent.

    Args:
        metrics_query_intent: JSON string with metrics query intent containing:
                            - description: Query description
                            - namespace: Prometheus namespace
                            - metric_name: (optional) Specific metric name
                            - aggregation: (optional) Aggregation function (rate, sum, avg, etc.)
                            - group_by: (optional) Labels to group by
                            - filters: (optional) Label filters

    Returns:
        JSON string with generated PromQL query and metadata.

    Example input:
        {
          "description": "API error rate over 5 minutes",
          "namespace": "production",
          "metric_name": "http_requests_total",
          "aggregation": "rate",
          "filters": {"status": "500"}
        }

    Example output:
        {
          "query": "rate(http_requests_total{status=\"500\"}[5m])",
          "success": true,
          "intent": {...}
        }
    """
    try:
        # Parse intent
        intent_data = json.loads(metrics_query_intent)
        intent = MetricsQueryIntent(**intent_data)

        # Get client and generate query
        client = _get_metrics_client()
        result = client.construct_promql_query(intent)

        return json.dumps(
            {
                **result,
                "intent": intent_data,
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON input: {e}", "query": "", "success": False}
        )
    except Exception as e:
        return json.dumps({"error": str(e), "query": "", "success": False})
