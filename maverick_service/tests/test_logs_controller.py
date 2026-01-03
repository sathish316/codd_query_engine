"""Unit tests for logs controller."""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from maverick_service.main import app
from maverick_engine.querygen_engine.logs.structured_outputs import LogsQueryResult

client = TestClient(app)


class TestLogsController:
    """Unit tests for logs controller endpoints."""

    @patch("maverick_service.api.controllers.logs_controller.get_client")
    def test_generate_logql_query_success(self, mock_get_client):
        """Test successful LogQL query generation."""
        mock_client = Mock()
        mock_result = LogsQueryResult(
            query='{service="payments", level="error"} |= "timeout"',
            success=True,
            error=None,
        )
        mock_client.logs.logql.construct_logql_query.return_value = mock_result
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/logs/logql/generate",
            json={
                "description": "Find timeout errors",
                "service": "payments",
                "patterns": [{"pattern": "timeout", "level": "error"}],
                "namespace": "production",
                "limit": 200,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["backend"] == "loki"
        assert data["error"] is None
        assert "payments" in data["query"]

    @patch("maverick_service.api.controllers.logs_controller.get_client")
    def test_generate_logql_query_failure(self, mock_get_client):
        """Test LogQL query generation failure."""
        mock_client = Mock()
        mock_result = LogsQueryResult(
            query="", success=False, error="Invalid log pattern"
        )
        mock_client.logs.logql.construct_logql_query.return_value = mock_result
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/logs/logql/generate",
            json={
                "description": "Invalid query",
                "service": "test-service",
                "patterns": [{"pattern": ""}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Invalid log pattern"

    @patch("maverick_service.api.controllers.logs_controller.get_client")
    def test_generate_splunk_query_success(self, mock_get_client):
        """Test successful Splunk query generation."""
        mock_client = Mock()
        mock_result = LogsQueryResult(
            query='search index=main service="api-gateway" level="error" "timeout"',
            success=True,
            error=None,
        )
        mock_client.logs.splunk.construct_spl_query.return_value = mock_result
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/logs/splunk/generate",
            json={
                "description": "Find timeout errors",
                "service": "api-gateway",
                "patterns": [{"pattern": "timeout", "level": "error"}],
                "limit": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["backend"] == "splunk"
        assert data["error"] is None
        assert "api-gateway" in data["query"]

    @patch("maverick_service.api.controllers.logs_controller.get_client")
    def test_generate_splunk_query_failure(self, mock_get_client):
        """Test Splunk query generation failure."""
        mock_client = Mock()
        mock_result = LogsQueryResult(
            query="", success=False, error="Invalid SPL syntax"
        )
        mock_client.logs.splunk.construct_spl_query.return_value = mock_result
        mock_get_client.return_value = mock_client

        response = client.post(
            "/api/logs/splunk/generate",
            json={
                "description": "Invalid query",
                "service": "test-service",
                "patterns": [{"pattern": "test"}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Invalid SPL syntax"

    def test_generate_logql_missing_service(self):
        """Test LogQL generation with missing service parameter."""
        response = client.post(
            "/api/logs/logql/generate",
            json={"description": "Test query", "patterns": [{"pattern": "error"}]},
        )
        assert response.status_code == 422

    def test_generate_logql_missing_patterns(self):
        """Test LogQL generation with missing patterns parameter."""
        response = client.post(
            "/api/logs/logql/generate",
            json={"description": "Test query", "service": "test-service"},
        )
        assert response.status_code == 422

    def test_generate_splunk_missing_service(self):
        """Test Splunk generation with missing service parameter."""
        response = client.post(
            "/api/logs/splunk/generate",
            json={"description": "Test query", "patterns": [{"pattern": "error"}]},
        )
        assert response.status_code == 422

    def test_generate_splunk_missing_patterns(self):
        """Test Splunk generation with missing patterns parameter."""
        response = client.post(
            "/api/logs/splunk/generate",
            json={"description": "Test query", "service": "test-service"},
        )
        assert response.status_code == 422
