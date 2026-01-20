"""Configuration for query generation cache."""

from pydantic import BaseModel


class QuerygenCacheConfig(BaseModel):
    """Configuration for query generation caching.

    Attributes:
        enabled: Whether caching is enabled
        store: Cache store type (currently only 'redis' supported)
        ttl_in_seconds: Time-to-live for cached entries in seconds
    """

    enabled: bool = False
    store: str = "redis"
    ttl_in_seconds: int = 1800
