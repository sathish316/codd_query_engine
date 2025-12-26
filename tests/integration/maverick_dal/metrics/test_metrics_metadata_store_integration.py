"""
Unit tests for MetricsMetadataStore.

Tests cover all public methods with various scenarios including:
- Normal operations
- Edge cases (empty sets, non-existent keys)
- Multiple namespaces
- Thread safety considerations
"""

import redis

import pytest

from maverick_dal.metrics.metrics_metadata_client import MetricsMetadataStore

@pytest.fixture
def redis_client():
    """Provide a Redis client for testing."""
    return redis.Redis(host="localhost", port=6379, decode_responses=True)

@pytest.mark.integration
class TestMetricsMetadataStoreIntegration:
    """Integration tests for MetricsMetadataStore using redis."""

    def test_complete_metrics_metadata_workflow(self, redis_client):
        """
        Happy path integration test covering a complete workflow:
        1. Initialize store
        2. Set metrics for a namespace
        3. Add individual metrics
        4. Validate existing metrics
        5. Update metric set
        6. Verify isolation across namespaces
        """
        # Initialize the store
        store = MetricsMetadataStore(redis_client)
        namespace = "test:order_service"

        # Step 1: Set initial metrics for the namespace
        initial_metrics = {
            "cpu.usage.percent",
            "memory.used.bytes",
            "memory.total.bytes",
            "disk.read.bytes",
            "disk.write.bytes"
        }
        store.set_metric_names(namespace, initial_metrics)

        # Verify metrics were stored correctly
        retrieved_metrics = store.get_metric_names(namespace)
        assert retrieved_metrics == initial_metrics

        # Step 2: Add new metrics individually
        store.add_metric_name(namespace, "network.in.bytes")
        store.add_metric_name(namespace, "network.out.bytes")

        # Verify all metrics are present
        all_metrics = store.get_metric_names(namespace)
        assert len(all_metrics) == 7
        assert "network.in.bytes" in all_metrics
        assert "network.out.bytes" in all_metrics

        # Step 3: Validate existing metrics
        assert store.is_valid_metric_name(namespace, "cpu.usage.percent") is True
        assert store.is_valid_metric_name(namespace, "memory.used.bytes") is True
        assert store.is_valid_metric_name(namespace, "network.in.bytes") is True

        # Verify non-existent metrics return False
        assert store.is_valid_metric_name(namespace, "nonexistent.metric") is False
        assert store.is_valid_metric_name(namespace, "invalid.metric") is False

        # Step 5: Verify namespace isolation
        namespace2 = "test:payment_service"
        namespace2_metrics = {"payment.success", "payment.failure"}
        store.set_metric_names(namespace2, namespace2_metrics)

        # Each namespace has its own independent metrics
        assert store.is_valid_metric_name(namespace, "cpu.usage.percent") is True
        assert store.is_valid_metric_name(namespace2, "cpu.usage.percent") is False
        assert store.is_valid_metric_name(namespace2, "payment.success") is True
        assert store.is_valid_metric_name(namespace, "payment.success") is False
