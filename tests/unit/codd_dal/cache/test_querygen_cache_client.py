"""Unit tests for QuerygenCacheClient."""

import pytest
from unittest.mock import Mock
from dataclasses import dataclass

from codd_dal.cache.querygen_cache_client import QuerygenCacheClient


@dataclass(frozen=True)
class MockMetricsQueryIntent:
    """Mock metrics query intent for testing."""
    metric: str
    intent_description: str
    meter_type: str = "gauge"
    window: str = "5m"


@dataclass
class MockLogQueryIntent:
    """Mock log query intent for testing."""
    description: str
    backend: str
    service: str
    namespace: str = None


class TestQuerygenCacheClient:
    """Tests for QuerygenCacheClient."""

    def test_build_key_format(self):
        """Test cache key format is correct."""
        mock_cache_client = Mock()
        client = QuerygenCacheClient(mock_cache_client)

        intent = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )

        key = client.get_querygen_cache_key("production", "promql", intent)

        # Key format: querygen#<namespace>#<query_type>#<intent_hash>
        assert key.startswith("querygen#production#promql#")
        assert len(key.split("#")) == 4

    def test_build_key_with_empty_namespace(self):
        """Test cache key uses 'default' for empty namespace."""
        mock_cache_client = Mock()
        client = QuerygenCacheClient(mock_cache_client)

        intent = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )

        key = client.get_querygen_cache_key("", "promql", intent)

        assert "querygen#default#promql#" in key

    def test_build_key_consistent_for_same_intent(self):
        """Test same intent produces same key."""
        mock_cache_client = Mock()
        client = QuerygenCacheClient(mock_cache_client)

        intent1 = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )
        intent2 = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )

        key1 = client.get_querygen_cache_key("production", "promql", intent1)
        key2 = client.get_querygen_cache_key("production", "promql", intent2)

        assert key1 == key2

    def test_build_key_different_for_different_intent(self):
        """Test different intent produces different key."""
        mock_cache_client = Mock()
        client = QuerygenCacheClient(mock_cache_client)

        intent1 = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )
        intent2 = MockMetricsQueryIntent(
            metric="http_errors_total",
            intent_description="error count"
        )

        key1 = client.get_querygen_cache_key("production", "promql", intent1)
        key2 = client.get_querygen_cache_key("production", "promql", intent2)

        assert key1 != key2

    def test_get_cached_query_hit(self):
        """Test get_cached_query returns query on cache hit."""
        mock_cache_client = Mock()
        mock_cache_client.get.return_value = "rate(http_requests_total[5m])"

        client = QuerygenCacheClient(mock_cache_client)

        intent = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )

        result = client.get_cached_query("production", "promql", intent)

        assert result == "rate(http_requests_total[5m])"
        mock_cache_client.get.assert_called_once()

    def test_get_cached_query_miss(self):
        """Test get_cached_query returns None on cache miss."""
        mock_cache_client = Mock()
        mock_cache_client.get.return_value = None

        client = QuerygenCacheClient(mock_cache_client)

        intent = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )

        result = client.get_cached_query("production", "promql", intent)

        assert result is None

    def test_cache_query_success(self):
        """Test cache_query stores query successfully."""
        mock_cache_client = Mock()
        mock_cache_client.put.return_value = True

        client = QuerygenCacheClient(mock_cache_client)

        intent = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )

        result = client.cache_query(
            namespace="production",
            query_type="promql",
            intent=intent,
            query="rate(http_requests_total[5m])"
        )

        assert result is True
        mock_cache_client.put.assert_called_once()

    def test_cache_query_with_custom_ttl(self):
        """Test cache_query uses custom TTL when provided."""
        mock_cache_client = Mock()
        mock_cache_client.put.return_value = True

        client = QuerygenCacheClient(mock_cache_client)

        intent = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )

        client.cache_query(
            namespace="production",
            query_type="promql",
            intent=intent,
            query="rate(http_requests_total[5m])",
            ttl=3600
        )

        # Verify put was called with the custom TTL
        call_args = mock_cache_client.put.call_args
        assert call_args[1].get("ttl") == 3600 or call_args[0][2] == 3600

    def test_invalidate_cached_query(self):
        """Test invalidate_cached_query deletes cached query."""
        mock_cache_client = Mock()
        mock_cache_client.delete.return_value = True

        client = QuerygenCacheClient(mock_cache_client)

        intent = MockMetricsQueryIntent(
            metric="http_requests_total",
            intent_description="total requests"
        )

        result = client.invalidate_cached_query("production", "promql", intent)

        assert result is True
        mock_cache_client.delete.assert_called_once()

    def test_logql_query_type(self):
        """Test cache key for LogQL query type."""
        mock_cache_client = Mock()
        client = QuerygenCacheClient(mock_cache_client)

        intent = MockLogQueryIntent(
            description="find errors",
            backend="loki",
            service="api-gateway"
        )

        key = client.get_querygen_cache_key("default", "logql", intent)

        assert "querygen#default#logql#" in key

    def test_splunk_query_type(self):
        """Test cache key for Splunk query type."""
        mock_cache_client = Mock()
        client = QuerygenCacheClient(mock_cache_client)

        intent = MockLogQueryIntent(
            description="find timeouts",
            backend="splunk",
            service="api-gateway"
        )

        key = client.get_querygen_cache_key("default", "splunk", intent)

        assert "querygen#default#splunk#" in key
