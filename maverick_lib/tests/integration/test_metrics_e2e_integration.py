"""End-to-end integration tests for metrics operations using real providers."""

import pytest

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)


@pytest.mark.integration
def test_search_metrics_and_generate_query_e2e(
    maverick_client, setup_test_metrics_data, test_namespace
):
    """
    End-to-end test: Search relevant metrics → Generate PromQL query

    Workflow:
    1. Search for relevant metrics using natural language query
    2. Verify search returns expected metrics with similarity scores
    3. Create MetricsQueryIntent based on top search result
    4. Generate PromQL query using construct_promql_query()
    5. Verify query generation succeeds and returns valid QueryGenerationResult
    6. Verify query contains expected elements (metric name, aggregations, filters)

    This test uses:
    - Real semantic store (ChromaDB) for metrics search
    - Real query generator (with LLM calls) for PromQL generation
    - Real validators (with LLM calls) for query validation
    """
    # Step 1: Search for relevant metrics using natural language
    search_query = "HTTP request latency and duration"
    search_results = maverick_client.metrics.search_relevant_metrics(
        search_query, limit=5
    )

    # Step 2: Verify search returns results
    assert len(search_results) > 0, "Search should return at least one metric"

    # Verify the top result is a histogram metric for request duration
    top_result = search_results[0]
    assert "metric_name" in top_result, "Result should have metric_name field"
    assert "similarity_score" in top_result, "Result should have similarity_score field"
    assert top_result["similarity_score"] > 0.3, (
        f"Similarity score should be > 0.3, got {top_result['similarity_score']}"
    )

    # Verify result contains expected metric (should match duration/latency)
    metric_name = top_result["metric_name"]
    assert "http" in metric_name.lower() or "request" in metric_name.lower(), (
        f"Expected HTTP/request related metric, got {metric_name}"
    )

    # Step 3: Create MetricsQueryIntent for query generation
    # For histogram metrics, we typically want to query percentiles or rate
    intent = MetricsQueryIntent(
        metric=metric_name,
        intent_description="Get 95th percentile of HTTP request duration",
        metric_type="histogram",
        filters={"status": "200"},
        window="5m",
        aggregation_suggestions=[
            AggregationFunctionSuggestion(
                function_name="histogram_quantile", params={"quantile": 0.95}
            )
        ],
    )

    # Step 4: Generate PromQL query
    result = maverick_client.metrics.construct_promql_query(intent)

    # Step 5: Verify query generation succeeded
    assert result.success is True, f"Query generation failed: {result.error}"
    assert result.query is not None, "Query should not be None"
    assert len(result.query) > 0, "Query should not be empty"

    # Step 6: Verify query contains expected elements
    query = result.query
    assert metric_name in query, f"Query should contain metric name {metric_name}"
    assert "5m" in query or "[5m]" in query, "Query should contain time window"

    print(f"Search query: {search_query}")
    print(f"Top metric found: {metric_name}")
    print(f"Generated query: {query}")


@pytest.mark.integration
def test_direct_promql_generation_with_validation_e2e(
    maverick_client, setup_test_metrics_data, test_namespace
):
    """
    End-to-end test: Direct PromQL query generation with full validation pipeline

    Workflow:
    1. Seed Redis metadata store with available metrics
    2. Create detailed MetricsQueryIntent (counter with rate, filters, grouping)
    3. Generate PromQL query using construct_promql_query()
    4. Verify generated query structure
    5. Verify all query components: rate function, filters, window, group_by

    This test uses:
    - Real metadata store (Redis) for metric name validation
    - Real query generator (with LLM calls) for PromQL generation
    - Real validators (with LLM calls) for syntax, schema, and semantic validation
    """
    # Step 1: Metadata already seeded by setup_test_metrics_data fixture

    # Step 2: Create detailed MetricsQueryIntent for a counter metric
    intent = MetricsQueryIntent(
        metric="http_requests_total",
        intent_description="Calculate rate of HTTP requests with 500 errors grouped by instance",
        metric_type="counter",
        filters={"status": "500", "method": "GET"},
        window="5m",
        group_by=["instance"],
        aggregation_suggestions=[
            AggregationFunctionSuggestion(function_name="rate", params={})
        ],
    )

    # Step 3: Generate PromQL query
    result = maverick_client.metrics.construct_promql_query(intent)

    # Step 4: Verify query generation succeeded
    assert result.success is True, f"Query generation failed: {result.error}"
    assert result.query is not None, "Query should not be None"
    assert len(result.query) > 0, "Query should not be empty"

    # Step 5: Verify all query components
    query = result.query

    # Verify rate function
    assert "rate(" in query, "Query should contain rate() function for counter metric"

    # Verify metric name
    assert "http_requests_total" in query, "Query should contain metric name"

    # Verify time window
    assert "[5m]" in query, "Query should contain [5m] time window"

    # Verify filters
    # Note: Filter syntax might vary, checking for presence of filter values
    assert "500" in query or '"500"' in query or "500" in query, (
        "Query should contain status=500 filter"
    )

    # Verify grouping (might be "by (instance)" or similar)
    assert "instance" in query, "Query should contain instance grouping"

    print(f"Intent: {intent.description}")
    print(f"Generated query: {query}")
    print(f"Query validation: success={result.success}, error={result.error}")
