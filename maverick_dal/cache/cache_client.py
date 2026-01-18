"""Generic cache client abstraction."""

import logging
from typing import Optional

import redis

logger = logging.getLogger(__name__)


class CacheClient:
    """Generic cache client for Redis-based caching.

    Provides basic get/put operations with TTL support.
    """

    def __init__(self, redis_client: redis.Redis, default_ttl: int = 1800):
        """Initialize cache client.

        Args:
            redis_client: Redis client instance
            default_ttl: Default TTL in seconds for cached entries
        """
        self.redis_client = redis_client
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[str]:
        """Retrieve a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        try:
            value = self.redis_client.get(key)
            if value is not None:
                logger.debug("Cache hit for key: %s", key)
                return value
            logger.debug("Cache miss for key: %s", key)
            return None
        except Exception as e:
            logger.warning("Cache get failed for key %s: %s", key, str(e))
            return None

    def put(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds (uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            effective_ttl = ttl if ttl is not None else self.default_ttl
            self.redis_client.setex(key, effective_ttl, value)
            logger.debug("Cache put successful for key: %s (TTL: %ds)", key, effective_ttl)
            return True
        except Exception as e:
            logger.warning("Cache put failed for key %s: %s", key, str(e))
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            result = self.redis_client.delete(key)
            logger.debug("Cache delete for key %s: %s", key, "deleted" if result else "not found")
            return result > 0
        except Exception as e:
            logger.warning("Cache delete failed for key %s: %s", key, str(e))
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.warning("Cache exists check failed for key %s: %s", key, str(e))
            return False
