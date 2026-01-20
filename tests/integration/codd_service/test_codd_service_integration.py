"""E2E integration tests for Codd Service REST APIs."""

import pytest
from fastapi.testclient import TestClient

from codd_service.main import app

client = TestClient(app)


@pytest.mark.integration
class TestCoddServiceMetricsIntegration:
    """E2E integration tests for metrics endpoints."""

    def test_search_metrics_e2e(self):
        """
        Test semantic metrics search endpoint end-to-end.

        This test makes a real request to the service which uses
        codd_lib to perform semantic search against ChromaDB.
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


@pytest.mark.integration
class TestCoddServiceEndpointValidation:
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

    def test_splunk_generate_missing_patterns(self):
        """Test Splunk generation with missing patterns field."""
        request_data = {
            "description": "Test query",
            "service": "test-service",
            # Missing patterns
        }

        response = client.post("/api/logs/splunk/generate", json=request_data)
        assert response.status_code == 422
