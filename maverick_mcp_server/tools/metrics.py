"""Metrics-related MCP tools."""

import json


async def search_relevant_metrics(problem_json: str, limit: int = 5) -> str:
    """Search for metrics relevant to an alert or incident.

    Args:
        problem_json: JSON string containing alert or incident data with at least a 'description' field.
                     Can include 'keywords', 'suggested_metrics', 'category', etc.
        limit: Maximum number of metrics to return (default: 5)

    Returns:
        JSON string with relevant metrics ranked by relevance score.

    Example input:
        {
          "description": "API experiencing high latency",
          "category": "performance",
          "keywords": ["latency", "api", "slow"]
        }

    Example output:
        {
          "metrics": [
            {
              "metric_name": "http_request_duration_seconds",
              "relevance_score": 0.8,
              "reason": "Matches 2 keyword(s) from source data"
            }
          ],
          "total_searched": 1523
        }
    """
    try:
        from maverick_dal.metrics.promql_client import PromQLClient
    except ImportError as e:
        return json.dumps(
            {"error": f"Prometheus client not available: {e}", "metrics": []}
        )

    try:
        # Parse input
        problem_data = json.loads(problem_json)

        # Extract search keywords
        keywords = []
        if "description" in problem_data:
            keywords.extend(problem_data["description"].lower().split())
        if "keywords" in problem_data:
            keywords.extend(problem_data["keywords"])
        if "suggested_metrics" in problem_data:
            keywords.extend(problem_data["suggested_metrics"])

        # Clean keywords
        keywords = list(
            set([k for k in keywords if len(k) > 3 and k not in {"the", "and", "for"}])
        )

        # Fetch available metrics
        prom_url = "http://localhost:9090"  # TODO: Make configurable
        with PromQLClient(prom_url, timeout=30.0) as client:
            all_metrics = client.get_label_values("__name__")

        # Score metrics by keyword overlap
        scored_metrics = []
        for metric in all_metrics:
            metric_lower = metric.lower()
            score = sum(1 for keyword in keywords if keyword in metric_lower)
            if score > 0:
                scored_metrics.append((score, metric))

        # Sort and take top N
        scored_metrics.sort(key=lambda x: (-x[0], x[1]))
        top_metrics = scored_metrics[:limit]

        # Build result
        results = [
            {
                "metric_name": metric,
                "relevance_score": (
                    min(score / len(keywords), 1.0) if keywords else 0.0
                ),
                "reason": f"Matches {score} keyword(s) from source data",
            }
            for score, metric in top_metrics
        ]

        return json.dumps(
            {
                "query": f"keywords: {', '.join(keywords[:5])}",
                "metrics": results,
                "total_searched": len(all_metrics),
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
        from maverick_engine.querygen_engine.metrics.imports import MetricsQueryIntent
        from maverick_engine.querygen_engine.agent.metrics.promql_query_generator_agent import (
            PromQLQueryGeneratorAgent,
        )
        from maverick_engine.querygen_engine.metrics.preprocessor.promql_querygen_preprocessor import (
            PromQLQuerygenPreprocessor,
        )
        from maverick_engine.validation_engine.metrics.promql_imports import (
            PromQLValidator,
        )
        from maverick_engine.agent_imports import ConfigManager, InstructionsManager
        from maverick_engine.utils.file_utils import expand_path
    except ImportError as e:
        return json.dumps(
            {
                "error": f"Query generation dependencies not available: {e}",
                "query": "",
                "success": False,
            }
        )

    try:
        # Parse intent
        intent_data = json.loads(metrics_query_intent)
        intent = MetricsQueryIntent(**intent_data)

        # Initialize components
        config_manager = ConfigManager(expand_path("$HOME/.maverick"), "config.yml")
        instructions_manager = InstructionsManager()
        preprocessor = PromQLQuerygenPreprocessor(config_manager, instructions_manager)
        validator = PromQLValidator(
            syntax_validator=None, schema_validator=None, semantics_validator=None
        )

        # Create agent and generate query
        agent = PromQLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            preprocessor=preprocessor,
            promql_validator=validator,
        )

        result = agent.generate_query(intent)

        return json.dumps(
            {
                "query": result.query,
                "intent": intent_data,
                "success": result.success,
                "error": result.error if hasattr(result, "error") else None,
            },
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON input: {e}", "query": "", "success": False}
        )
    except Exception as e:
        return json.dumps({"error": str(e), "query": "", "success": False})
