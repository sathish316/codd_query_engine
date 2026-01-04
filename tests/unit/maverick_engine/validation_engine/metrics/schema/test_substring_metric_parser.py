"""
Unit tests for SubstringMetricParser.

Tests cover:
- Happy path with metrics found as substrings
- No matches found
- Empty expression handling
- Namespace not set
- Multiple metrics matching
"""

import pytest
import fakeredis

from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.validation_engine.metrics.schema.substring_metric_parser import (
    SubstringMetricParser,
)


@pytest.fixture
def redis_client():
    """Provide a fake Redis client for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def metadata_store(redis_client):
    """Provide a MetricsMetadataStore instance with fake Redis."""
    return MetricsMetadataStore(redis_client)


class TestSubstringMetricParser:
    """Test suite for SubstringMetricParser."""

    def test_single_metric_found(self, metadata_store):
        """Test finding a single metric as substring."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total", "disk_io"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)
        parser.set_namespace(namespace)

        result = parser.parse("rate(cpu_usage[5m])")

        assert result == {"cpu_usage"}

    def test_multiple_metrics_found(self, metadata_store):
        """Test finding multiple metrics as substrings."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total", "disk_io"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)
        parser.set_namespace(namespace)

        result = parser.parse("cpu_usage + memory_total")

        assert result == {"cpu_usage", "memory_total"}

    def test_no_metrics_found(self, metadata_store):
        """Test when no metrics match as substrings."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)
        parser.set_namespace(namespace)

        result = parser.parse("rate(network_bytes[5m])")

        assert result == set()

    def test_empty_expression(self, metadata_store):
        """Test with empty expression."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)
        parser.set_namespace(namespace)

        result = parser.parse("")

        assert result == set()

    def test_namespace_not_set(self, metadata_store):
        """Test when namespace is not set."""
        parser = SubstringMetricParser(metadata_store)

        result = parser.parse("cpu_usage")

        assert result == set()

    def test_no_valid_metrics_in_namespace(self, metadata_store):
        """Test when namespace has no metrics."""
        namespace = "empty_ns"
        parser = SubstringMetricParser(metadata_store)
        parser.set_namespace(namespace)

        result = parser.parse("cpu_usage")

        assert result == set()

    def test_partial_metric_name_match(self, metadata_store):
        """Test that partial matches work (substring)."""
        namespace = "test_ns"
        # If a metric contains another as substring, both should match
        valid_metrics = {"cpu", "cpu_usage", "cpu_usage_percent"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)
        parser.set_namespace(namespace)

        # Expression contains "cpu_usage" which matches both "cpu", "cpu_usage"
        result = parser.parse("rate(cpu_usage[5m])")

        # All metrics that appear as substrings should be found
        assert "cpu" in result
        assert "cpu_usage" in result

    def test_namespace_change(self, metadata_store):
        """Test changing namespace between calls."""
        ns1 = "namespace1"
        ns2 = "namespace2"
        metadata_store.set_metric_names(ns1, {"metric_a", "metric_b"})
        metadata_store.set_metric_names(ns2, {"metric_x", "metric_y"})

        parser = SubstringMetricParser(metadata_store)

        # First call with ns1
        parser.set_namespace(ns1)
        result1 = parser.parse("metric_a")
        assert result1 == {"metric_a"}

        # Second call with ns2
        parser.set_namespace(ns2)
        result2 = parser.parse("metric_x")
        assert result2 == {"metric_x"}

        # metric_a should not be found in ns2
        result3 = parser.parse("metric_a")
        assert result3 == set()
