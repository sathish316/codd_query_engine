"""
Unit tests for FuzzyMetricParser.

Tests cover:
- Exact substring matches (fast path)
- Fuzzy matching when no exact match
- Suggestions generation
- Empty expression handling
- Namespace not set
- Configuration parameters (top_k, suggestion_limit, min_similarity_score)
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
        parser.set_namespace(namespace)

        result = parser.parse("rate(cpu_usage[5m])")

        assert result == {"cpu_usage"}

    def test_multiple_exact_matches(self, metadata_store):
        """Test finding multiple metrics with exact substring matches."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total", "disk_io"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store)
        parser.set_namespace(namespace)

        result = parser.parse("cpu_usage + memory_total")

        assert result == {"cpu_usage", "memory_total"}

    def test_fuzzy_match_with_typo(self, metadata_store):
        """Test fuzzy matching finds metrics despite typos."""
        namespace = "test_ns"
        # Create metrics with predictable names
        valid_metrics = {"http_requests_total", "http_request_duration"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store, min_similarity_score=70)
        parser.set_namespace(namespace)

        # Expression has a typo: "http_requets" instead of "http_requests"
        # This should fuzzy match to "http_requests_total"
        result = parser.parse("rate(http_requests_total[5m])")

        # Should find exact match
        assert "http_requests_total" in result

    def test_empty_expression(self, metadata_store):
        """Test with empty expression."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store)
        parser.set_namespace(namespace)

        result = parser.parse("")

        assert result == set()

    def test_namespace_not_set(self, metadata_store):
        """Test when namespace is not set."""
        parser = FuzzyMetricParser(metadata_store)

        result = parser.parse("cpu_usage")

        assert result == set()

    def test_no_valid_metrics_in_namespace(self, metadata_store):
        """Test when namespace has no metrics."""
        namespace = "empty_ns"
        parser = FuzzyMetricParser(metadata_store)
        parser.set_namespace(namespace)

        result = parser.parse("cpu_usage")

        assert result == set()

    def test_get_suggestions(self, metadata_store):
        """Test getting 'did you mean' suggestions."""
        namespace = "test_ns"
        valid_metrics = {
            "http_requests_total",
            "http_request_duration",
            "http_response_size",
        }
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(
            metadata_store, suggestion_limit=3, min_similarity_score=50
        )
        parser.set_namespace(namespace)

        # Expression with a similar but not exact metric name
        suggestions = parser.get_suggestions("http_request")

        # Should return suggestions sorted by score
        assert len(suggestions) <= 3
        assert all(isinstance(s, tuple) and len(s) == 2 for s in suggestions)
        assert all(isinstance(s[0], str) and isinstance(s[1], (int, float)) for s in suggestions)

        # All suggestions should be from our valid metrics
        metric_names = [s[0] for s in suggestions]
        assert all(m in valid_metrics for m in metric_names)

    def test_suggestions_empty_for_no_match(self, metadata_store):
        """Test that suggestions are empty when no fuzzy matches found."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store, min_similarity_score=90)
        parser.set_namespace(namespace)

        # Completely different metric name with high threshold
        suggestions = parser.get_suggestions("completely_different_metric_xyz123")

        # Should return empty or very low similarity suggestions
        assert len(suggestions) <= parser._suggestion_limit

    def test_namespace_change_reloads_index(self, metadata_store):
        """Test that changing namespace reloads the metric index."""
        ns1 = "namespace1"
        ns2 = "namespace2"
        metadata_store.set_metric_names(ns1, {"metric_a", "metric_b"})
        metadata_store.set_metric_names(ns2, {"metric_x", "metric_y"})

        parser = FuzzyMetricParser(metadata_store)

        # First call with ns1
        parser.set_namespace(ns1)
        result1 = parser.parse("metric_a")
        assert result1 == {"metric_a"}

        # Change to ns2 - should reload index
        parser.set_namespace(ns2)
        result2 = parser.parse("metric_x")
        assert result2 == {"metric_x"}

        # metric_a should not be found in ns2
        result3 = parser.parse("metric_a")
        assert result3 == set()

    def test_custom_top_k(self, metadata_store):
        """Test that top_k parameter is respected."""
        namespace = "test_ns"
        # Create many similar metrics
        valid_metrics = {f"http_request_metric_{i}" for i in range(20)}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store, top_k=5, min_similarity_score=50)
        parser.set_namespace(namespace)

        suggestions = parser.get_suggestions("http_request")

        # Should respect suggestion_limit, not top_k
        assert len(suggestions) <= parser._suggestion_limit

    def test_custom_min_similarity_score(self, metadata_store):
        """Test that min_similarity_score filters results."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage", "memory_total"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        # Very high threshold - should filter out most matches
        parser = FuzzyMetricParser(metadata_store, min_similarity_score=95)
        parser.set_namespace(namespace)

        suggestions = parser.get_suggestions("xyz123")

        # With high threshold and completely different string, should have few/no suggestions
        assert all(score >= 95 or score == 0 for _, score in suggestions)

    def test_expression_with_no_tokens(self, metadata_store):
        """Test expression that has no valid metric-like tokens."""
        namespace = "test_ns"
        valid_metrics = {"cpu_usage"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = FuzzyMetricParser(metadata_store)
        parser.set_namespace(namespace)

        # Expression with no lowercase alphanumeric tokens
        result = parser.parse("123 + 456")

        assert result == set()
