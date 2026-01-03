"""E2E integration tests for Maverick Service REST APIs."""

import pytest
from fastapi.testclient import TestClient

from maverick_service.main import app

client = TestClient(app)


@pytest.mark.integration
class TestMaverickServiceMetricsIntegration:
    """E2E integration tests for metrics endpoints."""

    def test_search_metrics_e2e(self):
        """
        Test semantic metrics search endpoint end-to-end.

        This test makes a real request to the service which uses
        maverick_lib to perform semantic search against ChromaDB.
        """
        request_data = {"query": "API request latency", "limit": 5}

        response = client.post("/api/metrics/search", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data
        assert isinstance(data["results"], list)
        assert data["count"] == len(data["results"])
        assert data["count"] <= 5

        # Validate result structure if results exist
        if data["results"]:
            result = data["results"][0]
            assert "metric_name" in result
            assert "similarity_score" in result

    @pytest.mark.skip(reason="taking lot of time")
    def test_generate_promql_query_e2e(self):
        """
        Test PromQL query generation endpoint end-to-end.

        This test makes a real request that uses LLM to generate
        a PromQL query with validation feedback loop.
        """
        request_data = {
            "description": "API error rate for payment service",
            "namespace": "production",
            "metric_name": "http_requests_total",
            "aggregation": "rate",
            "filters": {"service": "payments", "status": "500"},
        }

        response = client.post("/api/metrics/promql/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "success" in data
        assert "error" in data

        # If successful, query should be a non-empty string
        if data["success"]:
            assert isinstance(data["query"], str)
            assert len(data["query"]) > 0
            # PromQL query should contain the metric name
            assert "http_requests_total" in data["query"]


@pytest.mark.integration
class TestMaverickServiceLogsIntegration:
    """E2E integration tests for logs endpoints."""

    def test_generate_logql_query_e2e(self):
        """
        Test LogQL query generation endpoint end-to-end.

        This test makes a real request that uses LLM to generate
        a LogQL query for Loki.
        """
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

        response = client.post("/api/logs/logql/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "backend" in data
        assert "success" in data
        assert "error" in data
        assert data["backend"] == "loki"

        # If successful, query should be a non-empty string
        if data["success"]:
            assert isinstance(data["query"], str)
            assert len(data["query"]) > 0
            # LogQL query should reference the service
            assert "payments" in data["query"]

    @pytest.mark.skip(reason="Skipping Splunk-related tests - PydanticAI usage limit issue")
    def test_generate_splunk_query_e2e(self):
        """
        Test Splunk query generation endpoint end-to-end.

        This test makes a real request that uses LLM to generate
        a Splunk SPL query.
        """
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

        response = client.post("/api/logs/splunk/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "backend" in data
        assert "success" in data
        assert "error" in data
        assert data["backend"] == "splunk"

        # If successful, query should be a non-empty string
        if data["success"]:
            assert isinstance(data["query"], str)
            assert len(data["query"]) > 0
            # Splunk query should reference the service
            assert "api-gateway" in data["query"]


@pytest.mark.integration
class TestMaverickServiceEndpointValidation:
    """Test request validation for all endpoints."""

    def test_metrics_search_missing_query(self):
        """Test metrics search with missing query field."""
        request_data = {"limit": 5}

        response = client.post("/api/metrics/search", json=request_data)
        assert response.status_code == 422

    def test_promql_generate_missing_required_fields(self):
        """Test PromQL generation with missing required fields."""
        request_data = {
            "description": "Test query"
            # Missing namespace
        }

        response = client.post("/api/metrics/promql/generate", json=request_data)
        assert response.status_code == 422

    def test_logql_generate_missing_service(self):
        """Test LogQL generation with missing service field."""
        request_data = {
            "description": "Test query",
            "patterns": [{"pattern": "error"}],
            # Missing service
        }

        response = client.post("/api/logs/logql/generate", json=request_data)
        assert response.status_code == 422

    @pytest.mark.skip(reason="Skipping Splunk-related tests - PydanticAI usage limit issue")
    def test_splunk_generate_missing_patterns(self):
        """Test Splunk generation with missing patterns field."""
        request_data = {
            "description": "Test query",
            "service": "test-service",
            # Missing patterns
        }

        response = client.post("/api/logs/splunk/generate", json=request_data)
        assert response.status_code == 422
