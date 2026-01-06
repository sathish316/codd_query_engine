"""
Tests for PromQL client.
"""

import os
import pytest
from datetime import datetime, timedelta

from maverick_dal.metrics.promql_client import PromQLClient
from maverick_lib.config import PrometheusConfig


@pytest.mark.integration
class TestPromQLClientIntegration:
    """Integration tests for PromQLClient against a real Prometheus instance."""

    @pytest.fixture
    def prometheus_url(self):
        """Get Prometheus URL from environment or use default."""
        return os.getenv("PROMETHEUS_URL", "http://localhost:9090")

    @pytest.fixture
    def skip_if_no_prometheus(self, prometheus_url):
        """Skip test if Prometheus is not available."""
        try:
            config = PrometheusConfig(base_url=prometheus_url, timeout=5)
            with PromQLClient(config) as client:
                if not client.health_check():
                    pytest.skip("Prometheus is not healthy")
        except Exception:
            pytest.skip("Prometheus is not available")

    @pytest.mark.integration
    def test_promql_client_integration_complete_workflow(self, prometheus_url):
        """
        Test complete workflow for PromQLClient.

        This integration test verifies:
        1. Client initialization and connection
        2. Health check passes
        3. Metadata retrieval (labels)
        4. Query execution (instant query)
        5. Proper cleanup via context manager
        """
        config = PrometheusConfig(base_url=prometheus_url, timeout=30)
        with PromQLClient(config) as client:
            # Step 1: Verify Prometheus is healthy
            assert client.health_check() is True, "Prometheus health check failed"
            assert client.ready_check() is True, "Prometheus ready check failed"

            # Step 2: Get available label names
            label_names = client.get_label_names()
            assert isinstance(label_names, list), "Label names should be a list"
            assert len(label_names) > 0, "Expected at least one label name"
            assert "__name__" in label_names, "__name__ label should always be present"

            # Step 3: Get label values for __name__ (metric names)
            metric_names = client.get_label_values("__name__")
            assert isinstance(metric_names, list), "Metric names should be a list"
            assert len(metric_names) > 0, "Expected at least one metric"

            # Step 4: Execute instant query using the first available metric
            first_metric = metric_names[0]
            query_result = client.query_instant(first_metric)

            assert "resultType" in query_result, "Query result should have resultType"
            assert "result" in query_result, "Query result should have result"
            assert isinstance(query_result["result"], list), "Result should be a list"

            # Step 5: Get series for the metric
            series = client.get_series(match=[first_metric])
            assert isinstance(series, list), "Series should be a list"

            # Step 6: Execute range query over last 5 minutes
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=5)
            range_result = client.query_range(
                query=first_metric, start=start_time, end=end_time, step="1m"
            )

            assert "resultType" in range_result, (
                "Range query result should have resultType"
            )
            assert "result" in range_result, "Range query result should have result"
            assert range_result["resultType"] == "matrix", (
                "Range query should return matrix type"
            )

            # Step 7: Get metric metadata
            metadata = client.get_metric_metadata(metric=first_metric, limit=1)
            assert isinstance(metadata, dict), "Metadata should be a dictionary"
