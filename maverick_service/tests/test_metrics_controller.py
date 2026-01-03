"""Unit tests for metrics controller."""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from maverick_service.main import app
from maverick_engine.validation_engine.metrics.structured_outputs import SearchResult
from maverick_engine.querygen_engine.metrics.structured_outputs import PromQLQueryResult

client = TestClient(app)


class TestMetricsController:
    """Unit tests for metrics controller endpoints."""

    @patch("maverick_service.api.controllers.metrics_controller.get_client")
    def test_search_metrics_success(self, mock_get_client):
        """Test successful metrics search."""
        # Mock the client and response
        mock_client = Mock()
        mock_results = [
            SearchResult(
                metric_name="http_requests_total",
                metric_type="counter",
                description="Total HTTP requests",
                similarity_score=0.95,
            ),
            SearchResult(
                metric_name="http_request_duration_seconds",
                metric_type="histogram",
                description="HTTP request duration",
                similarity_score=0.88,
            ),
        ]
        mock_client.metrics.search_relevant_metrics.return_value = mock_results
        mock_get_client.return_value = mock_client

        # Make request
        response = client.post(
            "/api/metrics/search", json={"query": "HTTP requests", "limit": 5}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["metric_name"] == "http_requests_total"
        mock_client.metrics.search_relevant_metrics.assert_called_once_with(
            "HTTP requests", limit=5
        )

    @patch("maverick_service.api.controllers.metrics_controller.get_client")
    def test_search_metrics_empty_results(self, mock_get_client):
        """Test metrics search with no results."""
        mock_client = Mock()
        mock_client.metrics.search_relevant_metrics.return_value = []
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/metrics/search", json={"query": "nonexistent metric", "limit": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []

    @patch("maverick_service.api.controllers.metrics_controller.get_client")
    def test_generate_promql_query_success(self, mock_get_client):
        """Test successful PromQL query generation."""
        mock_client = Mock()
        mock_result = PromQLQueryResult(
            query='rate(http_requests_total{service="payments", status="500"}[5m])',
            success=True,
            error=None,
        )
        mock_client.metrics.construct_promql_query.return_value = mock_result
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/metrics/promql/generate",
            json={
                "description": "API error rate",
                "namespace": "production",
                "metric_name": "http_requests_total",
                "aggregation": "rate",
                "filters": {"service": "payments", "status": "500"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["error"] is None
        assert "http_requests_total" in data["query"]

    @patch("maverick_service.api.controllers.metrics_controller.get_client")
    def test_generate_promql_query_failure(self, mock_get_client):
        """Test PromQL query generation failure."""
        mock_client = Mock()
        mock_result = PromQLQueryResult(
            query="", success=False, error="Invalid metric name"
        )
        mock_client.metrics.construct_promql_query.return_value = mock_result
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/metrics/promql/generate",
            json={
                "description": "Invalid query",
                "namespace": "production",
                "metric_name": "invalid_metric",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Invalid metric name"

    def test_search_metrics_missing_query(self):
        """Test metrics search with missing query parameter."""
        response = client.post("/api/metrics/search", json={"limit": 5})
        assert response.status_code == 422

    def test_generate_promql_missing_namespace(self):
        """Test PromQL generation with missing namespace parameter."""
        response = client.post(
            "/api/metrics/promql/generate", json={"description": "Test query"}
        )
        assert response.status_code == 422
