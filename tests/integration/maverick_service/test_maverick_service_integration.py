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
