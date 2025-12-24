"""
Redis-based metrics metadata store.

Job:
1. store metrics metadata for a namespace. namespace is tenant x service name
2. used for schema validation of metric names
"""

from typing import Optional
import redis


class MetricsMetadataClient:
    """
    Client for managing metrics metadata in Redis.

    Args:
        redis_client: Redis client instance
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize metrics metadata client.

        Args:
            redis_client: Redis client instance
        """
        self.redis_client = redis_client

    def _get_key(self, namespace: str) -> str:
        """
        Generate Redis key for metrics metadata

        Args:
            namespace: namespace identifier

        Returns:
            Redis key string in format, metric_names is hardcoded since it stores all metric names for a namespace: <namespace>#metric_names
        """
        if namespace is None or namespace == "":
            namespace = "default"
        return f"{namespace}#metric_names"

    def set_metric_names(self, namespace: str, metric_names: set[str]) -> None:
        """
        Replace all metric names for a namespace.

        Args:
            namespace: namespace identifier
            metric_names: Set of metric names to store
        """
        key = self._get_key(namespace)

        # Delete existing key to replace all values
        self.redis_client.delete(key)

        # Add new metric names if set is not empty
        if metric_names:
            self.redis_client.sadd(key, *metric_names)

    def get_metric_names(self, namespace: str) -> set[str]:
        """
        Retrieve all metric names for a namespace.

        Args:
            namespace: namespace identifier

        Returns:
            Set of metric names, empty set if namespace doesn't exist
        """
        key = self._get_key(namespace)
        members = self.redis_client.smembers(key)

        # Handle bytes if decode_responses=False
        # if members and isinstance(next(iter(members)), bytes):
        #     return {member.decode('utf-8') for member in members}

        return members if members else set()

    def add_metric_name(self, namespace: str, metric_name: str) -> None:
        """
        Add a single metric name to an existing namespace.

        Creates namespace set if it doesn't exist.

        Args:
            namespace: namespace identifier
            metric_name: metric name to add
        """
        key = self._get_key(namespace)
        if metric_name is None or metric_name == "":
            raise ValueError("metric_name cannot be empty")
        self.redis_client.sadd(key, metric_name)

    def is_valid_metric_name(self, namespace: str, metric_name: str) -> bool:
        """
        Check if a metric name exists in a namespace.

        Args:
            namespace: namespace identifier
            metric_name: metric name to check

        Returns:
            True if metric name exists in namespace, False otherwise
        """
        key = self._get_key(namespace)
        return bool(self.redis_client.sismember(key, metric_name))
