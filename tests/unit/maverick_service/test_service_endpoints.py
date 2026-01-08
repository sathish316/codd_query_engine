"""Unit tests for Maverick Service REST API endpoints with mocked dependencies."""

from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from maverick_service.main import app
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    QueryGenerationResult,
)
from maverick_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult as LogQueryGenerationResult,
)

client = TestClient(app)


class TestServiceMetricsEndpoints:
    """Unit tests for metrics endpoints with mocked query generation."""

    @patch("maverick_service.api.controllers.metrics_controller.get_client")
    @pytest.mark.asyncio
    async def test_generate_promql_query_endpoint_success(self, mock_get_client):
        """
        Test PromQL generation endpoint with successful mocked query generation.

        Validates that the endpoint correctly handles successful query generation
        and returns the expected response structure.
        """
        # Arrange: Mock successful query generation
        mock_client = MagicMock()
        mock_client.metrics.construct_promql_query = AsyncMock(
            return_value=QueryGenerationResult(
                success=True,
                query='rate(http_requests_total{service="payments",status="500"}[5m])',
                error=None,
            )
        )
        mock_get_client.return_value = mock_client

        request_data = {
            "description": "API error rate for payment service",
            "namespace": "production",
            "metric_name": "http_requests_total",
            "aggregation": "rate",
            "filters": {"service": "payments", "status": "500"},
        }

        # Act: Call the endpoint
        response = client.post("/api/metrics/promql/generate", json=request_data)

        # Assert: Verify response structure
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["query"] == 'rate(http_requests_total{service="payments",status="500"}[5m])'
        assert data["error"] is None
        assert "http_requests_total" in data["query"]

    @patch("maverick_service.api.controllers.metrics_controller.get_client")
    @pytest.mark.asyncio
    async def test_generate_promql_query_endpoint_failure(self, mock_get_client):
        """
        Test PromQL generation endpoint with failed mocked query generation.

        Validates that the endpoint correctly handles query generation failures
        and returns appropriate error information.
        """
        # Arrange: Mock failed query generation
        mock_client = MagicMock()
        mock_client.metrics.construct_promql_query = AsyncMock(
            return_value=QueryGenerationResult(
                success=False,
                query=None,
                error="Invalid metric name",
            )
        )
        mock_get_client.return_value = mock_client

        request_data = {
            "description": "Test query",
            "namespace": "production",
            "metric_name": "invalid_metric",
            "aggregation": "rate",
        }

        # Act: Call the endpoint
        response = client.post("/api/metrics/promql/generate", json=request_data)

        # Assert: Verify error handling
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["query"] is None
        assert data["error"] == "Invalid metric name"


class TestServiceLogsEndpoints:
    """Unit tests for logs endpoints with mocked query generation."""

    @patch("maverick_service.api.controllers.logs_controller.get_client")
    @pytest.mark.asyncio
    async def test_generate_logql_query_endpoint_success(self, mock_get_client):
        """
        Test LogQL generation endpoint with successful mocked query generation.

        Validates that the endpoint correctly handles successful query generation
        and returns the expected response structure.
        """
        # Arrange: Mock successful query generation
        mock_client = MagicMock()
        mock_client.logs.logql.construct_logql_query = AsyncMock(
            return_value=LogQueryGenerationResult(
                success=True,
                query='{service="payments"} |= "error" or "timeout"',
                error=None,
            )
        )
        mock_get_client.return_value = mock_client

        request_data = {
            "description": "Find error logs in payment service",
            "service": "payments",
            "patterns": [
                {"pattern": "error", "level": "error"},
                {"pattern": "timeout"},
            ],
            "namespace": "production",
            "limit": 200,
        }

        # Act: Call the endpoint
        response = client.post("/api/logs/logql/generate", json=request_data)

        # Assert: Verify response structure
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["backend"] == "loki"
        assert data["query"] == '{service="payments"} |= "error" or "timeout"'
        assert data["error"] is None
        assert "payments" in data["query"]

    @patch("maverick_service.api.controllers.logs_controller.get_client")
    @pytest.mark.asyncio
    async def test_generate_logql_query_endpoint_failure(self, mock_get_client):
        """
        Test LogQL generation endpoint with failed mocked query generation.

        Validates that the endpoint correctly handles query generation failures.
        """
        # Arrange: Mock failed query generation
        mock_client = MagicMock()
        mock_client.logs.logql.construct_logql_query = AsyncMock(
            return_value=LogQueryGenerationResult(
                success=False,
                query=None,
                error="Invalid log pattern syntax",
            )
        )
        mock_get_client.return_value = mock_client

        request_data = {
            "description": "Test query",
            "service": "test-service",
            "patterns": [{"pattern": "invalid["}],
            "limit": 100,
        }

        # Act: Call the endpoint
        response = client.post("/api/logs/logql/generate", json=request_data)

        # Assert: Verify error handling
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["query"] is None
        assert data["error"] == "Invalid log pattern syntax"

    @patch("maverick_service.api.controllers.logs_controller.get_client")
    @pytest.mark.asyncio
    async def test_generate_splunk_query_endpoint_success(self, mock_get_client):
        """
        Test Splunk SPL generation endpoint with successful mocked query generation.

        Validates that the endpoint correctly handles successful query generation
        and returns the expected response structure.
        """
        # Arrange: Mock successful query generation
        mock_client = MagicMock()
        mock_client.logs.splunk.construct_spl_query = AsyncMock(
            return_value=LogQueryGenerationResult(
                success=True,
                query='search service="api-gateway" (timeout OR "connection refused") | head 100',
                error=None,
            )
        )
        mock_get_client.return_value = mock_client

        request_data = {
            "description": "Search for timeout errors",
            "service": "api-gateway",
            "patterns": [
                {"pattern": "timeout", "level": "error"},
                {"pattern": "connection refused"},
            ],
            "default_level": "error",
            "limit": 100,
        }

        # Act: Call the endpoint
        response = client.post("/api/logs/splunk/generate", json=request_data)

        # Assert: Verify response structure
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["backend"] == "splunk"
        assert data["query"] == 'search service="api-gateway" (timeout OR "connection refused") | head 100'
        assert data["error"] is None
        assert "api-gateway" in data["query"]

    @patch("maverick_service.api.controllers.logs_controller.get_client")
    @pytest.mark.asyncio
    async def test_generate_splunk_query_endpoint_failure(self, mock_get_client):
        """
        Test Splunk SPL generation endpoint with failed mocked query generation.

        Validates that the endpoint correctly handles query generation failures.
        """
        # Arrange: Mock failed query generation
        mock_client = MagicMock()
        mock_client.logs.splunk.construct_spl_query = AsyncMock(
            return_value=LogQueryGenerationResult(
                success=False,
                query=None,
                error="Splunk syntax validation failed",
            )
        )
        mock_get_client.return_value = mock_client

        request_data = {
            "description": "Test query",
            "service": "test-service",
            "patterns": [{"pattern": "error"}],
            "limit": 100,
        }

        # Act: Call the endpoint
        response = client.post("/api/logs/splunk/generate", json=request_data)

        # Assert: Verify error handling
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["query"] is None
        assert data["error"] == "Splunk syntax validation failed"
