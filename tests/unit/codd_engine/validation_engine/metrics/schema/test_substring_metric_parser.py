"""
Unit tests for SubstringMetricParser.

Tests cover:
- Happy path with metrics found as substrings
- No matches found
- Empty expression handling
- Namespace not provided
- Multiple metrics matching
"""

import pytest
import fakeredis

from codd_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from codd_engine.validation_engine.metrics.schema.substring_metric_parser import (
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

        result = parser.parse("rate(cpu_usage[5m])", namespace)

        assert result == {"cpu_usage"}

    def test_first_metric_found(self, metadata_store):
        """Test that only first metric match is returned."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total", "disk_io"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)

        result = parser.parse("cpu_usage + memory_total", namespace)

        # Should return only the first match found
        assert len(result) == 1
        assert result.issubset(valid_metrics)

    def test_no_metrics_found(self, metadata_store):
        """Test when no metrics match as substrings."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)

        result = parser.parse("rate(network_bytes[5m])", namespace)

        assert result == set()

    def test_empty_expression(self, metadata_store):
        """Test with empty expression."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)

        result = parser.parse("", namespace)

        assert result == set()

    def test_namespace_not_provided(self, metadata_store):
        """Test when namespace is not provided."""
        parser = SubstringMetricParser(metadata_store)

        result = parser.parse("cpu_usage")

        assert result == set()

    def test_no_valid_metrics_in_namespace(self, metadata_store):
        """Test when namespace has no metrics."""
        namespace = "empty_ns"
        parser = SubstringMetricParser(metadata_store)

        result = parser.parse("cpu_usage", namespace)

        assert result == set()

    def test_partial_metric_name_match(self, metadata_store):
        """Test that partial matches work (substring)."""
        namespace = "test_ns"
        # If a metric contains another as substring, first match is returned
        valid_metrics = {"cpu", "cpu_usage", "cpu_usage_percent"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = SubstringMetricParser(metadata_store)

        # Expression contains "cpu_usage" which matches multiple metrics
        result = parser.parse("rate(cpu_usage[5m])", namespace)

        # Should return only first match (one of the valid metrics)
        assert len(result) == 1
        assert result.issubset(valid_metrics)

    def test_namespace_caching(self, metadata_store):
        """Test that metric index is cached per namespace."""
        ns1 = "namespace1"
        ns2 = "namespace2"
        metadata_store.set_metric_names(ns1, {"metric_a", "metric_b"})
        metadata_store.set_metric_names(ns2, {"metric_x", "metric_y"})

        parser = SubstringMetricParser(metadata_store)

        # First call with ns1
        result1 = parser.parse("metric_a", ns1)
        assert result1 == {"metric_a"}

        # Second call with ns2
        result2 = parser.parse("metric_x", ns2)
        assert result2 == {"metric_x"}

        # metric_a should not be found in ns2
        result3 = parser.parse("metric_a", ns2)
        assert result3 == set()

        # Verify caching by checking internal state
        assert ns1 in parser._metric_index_by_namespace
        assert ns2 in parser._metric_index_by_namespace
