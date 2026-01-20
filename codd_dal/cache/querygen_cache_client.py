"""Query generation cache client."""

import hashlib
import json
import logging
from dataclasses import asdict
from typing import Optional, Literal

from codd_dal.cache.cache_client import CacheClient

logger = logging.getLogger(__name__)

QueryType = Literal["promql", "logql", "splunk"]


class QuerygenCacheClient:
    """Cache client for query generation results.

    Handles cache key generation and query result caching.
    Cache key format: querygen#<namespace>#<query_type>#<intent_hash>
    """

    KEY_PREFIX = "querygen"

    def __init__(self, cache_client: CacheClient):
        """Initialize querygen cache client.

        Args:
            cache_client: Underlying cache client
        """
        self.cache_client = cache_client

    def _query_intent_hash(self, intent: object) -> str:
        """Generate a consistent hash for a query intent.

        Args:
            intent: Query intent dataclass

        Returns:
            SHA256 hash of the intent
        """
        # Convert dataclass to dict and sort keys for consistent hashing
        if hasattr(intent, "__dict__"):
            intent_dict = intent.__dict__
        else:
            intent_dict = asdict(intent)

        # Sort and serialize to JSON for consistent hashing
        intent_json = json.dumps(intent_dict, sort_keys=True, default=str)
        return hashlib.sha256(intent_json.encode()).hexdigest()[:16]

    def _build_key(self, namespace: str, query_type: QueryType, intent: object) -> str:
        """Build cache key for a query intent.

        Args:
            namespace: Namespace identifier
            query_type: Type of query (promql, logql, splunk)
            intent: Query intent dataclass

        Returns:
            Cache key in format: querygen#<namespace>#<query_type>#<intent_hash>
        """
        effective_namespace = namespace if namespace else "default"
        intent_hash = self._query_intent_hash(intent)
        return f"{self.KEY_PREFIX}#{effective_namespace}#{query_type}#{intent_hash}"

    def get_querygen_cache_key(self, namespace: str, query_type: QueryType, intent: object) -> str:
        """Get the cache key for a query intent (for logging purposes).

        Args:
            namespace: Namespace identifier
            query_type: Type of query (promql, logql, splunk)
            intent: Query intent dataclass

        Returns:
            Cache key in format: querygen#<namespace>#<query_type>#<intent_hash>
        """
        return self._build_key(namespace, query_type, intent)

    def get_cached_query(
        self, namespace: str, query_type: QueryType, intent: object
    ) -> Optional[str]:
        """Retrieve a cached query result.

        Args:
            namespace: Namespace identifier
            query_type: Type of query (promql, logql, splunk)
            intent: Query intent dataclass

        Returns:
            Cached query string if found, None otherwise
        """
        key = self._build_key(namespace, query_type, intent)
        result = self.cache_client.get(key)
        if result:
            logger.info(
                "Cache HIT for %s query in namespace '%s'", query_type.upper(), namespace
            )
        else:
            logger.info(
                "Cache MISS for %s query in namespace '%s'", query_type.upper(), namespace
            )
        return result

    def cache_query(
        self,
        namespace: str,
        query_type: QueryType,
        intent: object,
        query: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache a generated query result.

        Args:
            namespace: Namespace identifier
            query_type: Type of query (promql, logql, splunk)
            intent: Query intent dataclass
            query: Generated query to cache
            ttl: Optional TTL in seconds

        Returns:
            True if cached successfully, False otherwise
        """
        key = self._build_key(namespace, query_type, intent)
        success = self.cache_client.put(key, query, ttl)
        if success:
            logger.info(
                "Cached %s query for namespace '%s'", query_type.upper(), namespace
            )
        return success

    def invalidate_cached_query(
        self, namespace: str, query_type: QueryType, intent: object
    ) -> bool:
        """Invalidate a cached query.

        Args:
            namespace: Namespace identifier
            query_type: Type of query (promql, logql, splunk)
            intent: Query intent dataclass

        Returns:
            True if invalidated successfully, False otherwise
        """
        key = self._build_key(namespace, query_type, intent)
        return self.cache_client.delete(key)
