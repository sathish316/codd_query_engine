"""Unit tests for MetricsClient operations with mocked dependencies."""

from unittest.mock import Mock, AsyncMock, patch
import pytest

from maverick_lib import MaverickClient, MaverickConfig
from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    QueryGenerationResult,
)


@pytest.fixture
def mock_config():
    """Create a mock MaverickConfig."""
    return MaverickConfig(
        prometheus={"base_url": "http://test-prometheus:9090"},
        loki={"base_url": "http://test-loki:3100"},
    )


@pytest.fixture
def mock_promql_client():
    """Create a mock MetricsPromQLClient."""
    mock_client = Mock()
    mock_client.search_relevant_metrics = Mock(
        return_value=[
            {
                "metric_name": "http_request_duration_seconds",
                "similarity_score": 0.85,
                "metadata": {"type": "histogram"},
            },
            {
                "metric_name": "http_requests_total",
                "similarity_score": 0.75,
                "metadata": {"type": "counter"},
            },
        ]
    )
    mock_client.construct_promql_query = AsyncMock(
        return_value=QueryGenerationResult(
            success=True,
            query='rate(http_requests_total{status="500",method="GET"}[5m]) by (instance)',
            error=None,
        )
    )
    return mock_client


def test_search_metrics_with_mocked_store(mock_config):
    """
    Test metrics search with mocked semantic store.

    Verifies that search_relevant_metrics returns expected structure
    without making actual LLM or database calls.
    """
    # Arrange: Create client with mocked PromQL client
    with patch("maverick_lib.client.metrics_client.MetricsPromQLClient") as MockPromQLClient:
        mock_promql = Mock()
        mock_promql.search_relevant_metrics.return_value = [
            {
                "metric_name": "http_request_duration_seconds",
                "similarity_score": 0.85,
                "metadata": {"type": "histogram"},
            }
        ]
        MockPromQLClient.return_value = mock_promql

        client = MaverickClient(mock_config)

        # Act: Search for relevant metrics
        search_query = "HTTP request latency and duration"
        results = client.metrics.search_relevant_metrics(search_query, limit=5)

        # Assert: Verify search was called correctly
        mock_promql.search_relevant_metrics.assert_called_once_with(search_query, 5)

        # Assert: Verify results structure
        assert len(results) > 0
        assert "metric_name" in results[0]
        assert "similarity_score" in results[0]
        assert results[0]["similarity_score"] > 0.3


@pytest.mark.asyncio
async def test_promql_generation_with_mocked_validator(mock_config):
    """
    Test PromQL query generation with mocked validator.

    Verifies that construct_promql_query returns expected structure
    without making actual LLM calls.
    """
    # Arrange: Create client with mocked PromQL client
    with patch("maverick_lib.client.metrics_client.MetricsPromQLClient") as MockPromQLClient:
        mock_promql = Mock()
        mock_promql.construct_promql_query = AsyncMock(
            return_value=QueryGenerationResult(
                success=True,
                query='rate(http_requests_total{status="500",method="GET"}[5m]) by (instance)',
                error=None,
            )
        )
        MockPromQLClient.return_value = mock_promql

        client = MaverickClient(mock_config)

        # Arrange: Create MetricsQueryIntent
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

        # Act: Generate PromQL query
        result = await client.metrics.construct_promql_query(intent)

        # Assert: Verify generation was called correctly
        mock_promql.construct_promql_query.assert_called_once()

        # Assert: Verify result structure
        assert result.success is True
        assert result.query is not None
        assert len(result.query) > 0
        assert "rate(" in result.query
        assert "http_requests_total" in result.query
        assert "500" in result.query
        assert "instance" in result.query
