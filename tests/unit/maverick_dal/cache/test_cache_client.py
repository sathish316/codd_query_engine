"""Unit tests for CacheClient."""

import pytest
from unittest.mock import Mock, patch

from maverick_dal.cache.cache_client import CacheClient


class TestCacheClient:
    """Tests for CacheClient."""

    def test_get_cache_hit(self):
        """Test cache get returns value on cache hit."""
        mock_redis = Mock()
        mock_redis.get.return_value = "cached_value"

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.get("test_key")

        assert result == "cached_value"
        mock_redis.get.assert_called_once_with("test_key")

    def test_get_cache_miss(self):
        """Test cache get returns None on cache miss."""
        mock_redis = Mock()
        mock_redis.get.return_value = None

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.get("test_key")

        assert result is None
        mock_redis.get.assert_called_once_with("test_key")

    def test_get_handles_exception(self):
        """Test cache get returns None on exception."""
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis error")

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.get("test_key")

        assert result is None

    def test_put_with_default_ttl(self):
        """Test cache put uses default TTL."""
        mock_redis = Mock()
        mock_redis.setex.return_value = True

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.put("test_key", "test_value")

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 1800, "test_value")

    def test_put_with_custom_ttl(self):
        """Test cache put uses custom TTL when provided."""
        mock_redis = Mock()
        mock_redis.setex.return_value = True

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.put("test_key", "test_value", ttl=3600)

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 3600, "test_value")

    def test_put_handles_exception(self):
        """Test cache put returns False on exception."""
        mock_redis = Mock()
        mock_redis.setex.side_effect = Exception("Redis error")

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.put("test_key", "test_value")

        assert result is False

    def test_delete_existing_key(self):
        """Test cache delete returns True for existing key."""
        mock_redis = Mock()
        mock_redis.delete.return_value = 1

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    def test_delete_nonexistent_key(self):
        """Test cache delete returns False for non-existent key."""
        mock_redis = Mock()
        mock_redis.delete.return_value = 0

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.delete("test_key")

        assert result is False

    def test_exists_returns_true(self):
        """Test cache exists returns True when key exists."""
        mock_redis = Mock()
        mock_redis.exists.return_value = 1

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.exists("test_key")

        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    def test_exists_returns_false(self):
        """Test cache exists returns False when key does not exist."""
        mock_redis = Mock()
        mock_redis.exists.return_value = 0

        client = CacheClient(mock_redis, default_ttl=1800)
        result = client.exists("test_key")

        assert result is False
