"""
Unit tests for MetricsMetadataClient.

Tests cover all public methods with various scenarios including:
- Normal operations
- Edge cases (empty sets, non-existent keys)
- Multiple namespaces
- Thread safety considerations
"""

import pytest
import fakeredis

from maverick_dal.metrics.metrics_metadata_client import MetricsMetadataClient


@pytest.fixture
def redis_client():
    """Provide a fake Redis client for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def client(redis_client):
    """Provide a MetricsMetadataClient instance with fake Redis."""
    return MetricsMetadataClient(redis_client)


class TestMetricsMetadataClient:
    """Test suite for MetricsMetadataClient."""

    def test_get_key_format(self, client):
        """Test that key format follows <namespace>#metric_names pattern."""
        assert client._get_key("foo") == "foo#metric_names"
        assert client._get_key("bar") == "bar#metric_names"

    def test_set_metric_names_replaces_existing(self, client):
        """Test that set_metric_names replaces existing values."""
        namespace = "test_namespace"
        original_names = {"metric1", "metric2", "metric3"}
        new_names = {"metric4", "metric5"}

        # Set initial metrics
        client.set_metric_names(namespace, original_names)
        assert client.get_metric_names(namespace) == original_names

        # Replace with new metrics
        client.set_metric_names(namespace, new_names)
        result = client.get_metric_names(namespace)

        assert result == new_names
        assert "metric1" not in result
        assert "metric2" not in result
        assert "metric3" not in result

    def test_get_metric_names_nonexistent_namespace(self, client):
        """Test getting metrics from non-existent namespace returns empty set."""
        result = client.get_metric_names("nonexistent_namespace")

        assert result == set()
        assert isinstance(result, set)

    def test_get_metric_names_empty_namespace(self, client):
        """Test getting metrics with empty string namespace."""
        namespace = ""
        metric_names = {"metric1", "metric2"}

        client.set_metric_names(namespace, metric_names)
        result = client.get_metric_names(namespace)

        assert result == metric_names

    def test_add_metric_name_to_existing_set(self, client):
        """Test adding a metric to existing namespace."""
        namespace = "test_namespace"
        initial_names = {"metric1", "metric2"}

        client.set_metric_names(namespace, initial_names)
        client.add_metric_name(namespace, "metric3")

        result = client.get_metric_names(namespace)
        assert result == {"metric1", "metric2", "metric3"}

    def test_add_metric_name_duplicate(self, client):
        """Test adding duplicate metric name is idempotent."""
        namespace = "test_namespace"

        client.add_metric_name(namespace, "metric1")
        client.add_metric_name(namespace, "metric1")
        client.add_metric_name(namespace, "metric1")

        result = client.get_metric_names(namespace)
        assert result == {"metric1"}
        assert len(result) == 1

    def test_is_valid_metric_name(self, client):
        """Test validation returns True for existing metric, False for non-existent metric."""
        namespace = "test_namespace"
        metric_names = {"cpu.usage", "memory.total"}

        client.set_metric_names(namespace, metric_names)

        assert client.is_valid_metric_name(namespace, "cpu.usage") is True
        assert client.is_valid_metric_name(namespace, "memory.total") is True
        assert client.is_valid_metric_name(namespace, "disk.io") is False
        assert client.is_valid_metric_name(namespace, "network.bytes") is False

    def test_multiple_namespaces_isolation(self, client):
        """Test that different namespaces are isolated."""
        namespace1 = "namespace1"
        namespace2 = "namespace2"
        metrics1 = {"metric_a", "metric_b"}
        metrics2 = {"metric_x", "metric_y"}

        client.set_metric_names(namespace1, metrics1)
        client.set_metric_names(namespace2, metrics2)

        result1 = client.get_metric_names(namespace1)
        result2 = client.get_metric_names(namespace2)

        assert result1 == metrics1
        assert result2 == metrics2
        assert result1.isdisjoint(result2)

        # Verify cross-namespace validation
        assert client.is_valid_metric_name(namespace1, "metric_a") is True
        assert client.is_valid_metric_name(namespace1, "metric_x") is False
        assert client.is_valid_metric_name(namespace2, "metric_x") is True
        assert client.is_valid_metric_name(namespace2, "metric_a") is False

    def test_empty_metric_name_string(self, client):
        """Test that empty string metric name raises ValueError."""
        namespace = "test_namespace"

        with pytest.raises(ValueError, match="metric_name cannot be empty"):
            client.add_metric_name(namespace, "")
