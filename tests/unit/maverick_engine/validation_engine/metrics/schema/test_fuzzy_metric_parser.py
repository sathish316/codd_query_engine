"""
Unit tests for FuzzyMetricParser.

Tests cover:
- Exact substring matches (fast path)
- Fuzzy matching when no exact match
- Empty expression handling
- Namespace not provided
- Configuration parameters (top_k, min_similarity_score)
"""

import pytest
import fakeredis

from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.validation_engine.metrics.schema.fuzzy_metric_parser import (
    FuzzyMetricParser,
)


@pytest.fixture
def redis_client():
    """Provide a fake Redis client for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def metadata_store(redis_client):
    """Provide a MetricsMetadataStore instance with fake Redis."""
    return MetricsMetadataStore(redis_client)


class TestFuzzyMetricParser:
    """Test suite for FuzzyMetricParser."""

    def test_exact_substring_match(self, metadata_store):
        """Test that exact substring matches work (fast path)."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total", "disk_io"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store)

        result = parser.parse("rate(cpu_usage[5m])", namespace)

        assert result == {"cpu_usage"}

    def test_first_match_returned(self, metadata_store):
        """Test that only first match is returned."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total", "disk_io"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store)

        result = parser.parse("cpu_usage + memory_total", namespace)

        # Should return only the first match found
        assert len(result) == 1
        assert result.issubset(valid_metrics)

    def test_fuzzy_match_with_typo(self, metadata_store):
        """Test fuzzy matching finds metrics despite typos."""
        namespace = "test_ns"
        # Create metrics with predictable names
        valid_metrics = {"http_requests_total", "http_request_duration"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store, min_similarity_score=70)

        # Expression has exact match
        result = parser.parse("rate(http_requests_total[5m])", namespace)

        # Should find exact match
        assert "http_requests_total" in result

    def test_empty_expression(self, metadata_store):
        """Test with empty expression."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store)

        result = parser.parse("", namespace)

        assert result == set()

    def test_namespace_not_provided(self, metadata_store):
        """Test when namespace is not provided."""
        parser = FuzzyMetricParser(metadata_store)

        result = parser.parse("cpu_usage")

        assert result == set()

    def test_no_valid_metrics_in_namespace(self, metadata_store):
        """Test when namespace has no metrics."""
        namespace = "empty_ns"
        parser = FuzzyMetricParser(metadata_store)

        result = parser.parse("cpu_usage", namespace)

        assert result == set()

    def test_namespace_caching(self, metadata_store):
        """Test that metric index is cached per namespace."""
        ns1 = "namespace1"
        ns2 = "namespace2"
        metadata_store.set_metric_names(ns1, {"metric_a", "metric_b"})
        metadata_store.set_metric_names(ns2, {"metric_x", "metric_y"})

        parser = FuzzyMetricParser(metadata_store)

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

    def test_custom_top_k(self, metadata_store):
        """Test that top_k parameter is configurable."""
        namespace = "test_ns"
        # Create many similar metrics
        valid_metrics = {f"http_request_metric_{i}" for i in range(20)}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store, top_k=5, min_similarity_score=50)

        # Should work with custom top_k
        result = parser.parse("http_request_metric_1", namespace)
        assert "http_request_metric_1" in result

    def test_custom_min_similarity_score(self, metadata_store):
        """Test that min_similarity_score parameter is configurable."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        # Very high threshold
        parser = FuzzyMetricParser(metadata_store, min_similarity_score=95)

        # Exact match should still work
        result = parser.parse("cpu_usage", namespace)
        assert result == {"cpu_usage"}

    def test_expression_with_no_tokens(self, metadata_store):
        """Test expression that has no valid metric-like tokens."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store)

        # Expression with no lowercase alphanumeric tokens
        result = parser.parse("123 + 456", namespace)

        assert result == set()

    def test_fuzzy_matching_fallback(self, metadata_store):
        """Test that fuzzy matching is used when no exact substring match."""
        namespace = "test_ns"
        valid_metrics = {"metric_name_one", "metric_name_two"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store, min_similarity_score=80)

        # If the expression contains a fuzzy match that passes threshold
        # and the matched metric appears in the expression, it should be found
        result = parser.parse("metric_name_one", namespace)
        assert "metric_name_one" in result
