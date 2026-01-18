"""Provider module for cache client dependencies."""

from typing import Optional

import redis

from maverick_lib.config import MaverickConfig
from maverick_dal.cache import CacheClient, QuerygenCacheClient


class CacheModule:
    """Factory for cache-related dependencies."""

    _querygen_cache_client: Optional[QuerygenCacheClient] = None

    @classmethod
    def get_querygen_cache_client(cls, config: MaverickConfig) -> Optional[QuerygenCacheClient]:
        """
        Get or create QuerygenCacheClient if caching is enabled.

        Args:
            config: MaverickConfig instance

        Returns:
            QuerygenCacheClient if caching is enabled, None otherwise
        """
        if not config.querygen_cache.enabled:
            return None

        if cls._querygen_cache_client is None:
            redis_client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db,
                decode_responses=config.redis.decode_responses,
            )
            cache_client = CacheClient(
                redis_client=redis_client,
                default_ttl=config.querygen_cache.ttl_in_seconds,
            )
            cls._querygen_cache_client = QuerygenCacheClient(cache_client)
        return cls._querygen_cache_client

    @classmethod
    def reset(cls) -> None:
        """Reset the cached client instance (useful for testing)."""
        cls._querygen_cache_client = None
