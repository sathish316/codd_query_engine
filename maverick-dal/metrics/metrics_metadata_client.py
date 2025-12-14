"""
Redis-based metrics metadata store for caching and validating metric names.

This module provides a client for managing metrics metadata using Redis SET data structure.
Each namespace has its own set of metric names stored with key format: <namespace>#metric_names
"""

from typing import Optional
import redis


class MetricsMetadataClient:
    """
    Client for managing metrics metadata in Redis.

    Provides methods to store, retrieve, and validate metric names per namespace.
    Uses Redis SET data structure for fast membership checks.

    Args:
        redis_client: Redis client instance (should have decode_responses=True for string handling)
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize the metrics metadata client.

        Args:
            redis_client: Redis client instance for data operations
        """
        self.redis_client = redis_client

    def _get_key(self, namespace: str) -> str:
        """
        Generate Redis key for a namespace's metric names.

        Args:
            namespace: The namespace identifier

        Returns:
            Redis key string in format: <namespace>#metric_names
        """
        return f"{namespace}#metric_names"

    def set_metric_names(self, namespace: str, metric_names: set[str]) -> None:
        """
        Replace all metric names for a namespace.

        Deletes existing metric names and sets new ones atomically.
        If metric_names is empty, only deletion occurs (clearing the namespace).

        Args:
            namespace: The namespace identifier
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
            namespace: The namespace identifier

        Returns:
            Set of metric names, empty set if namespace doesn't exist
        """
        key = self._get_key(namespace)
        members = self.redis_client.smembers(key)

        # Handle bytes if decode_responses=False
        if members and isinstance(next(iter(members)), bytes):
            return {member.decode('utf-8') for member in members}

        return members if members else set()

    def add_metric_name(self, namespace: str, metric_name: str) -> None:
        """
        Add a single metric name to an existing namespace.

        Creates the namespace set if it doesn't exist.

        Args:
            namespace: The namespace identifier
            metric_name: The metric name to add
        """
        key = self._get_key(namespace)
        self.redis_client.sadd(key, metric_name)

    def is_valid_metric_name(self, namespace: str, metric_name: str) -> bool:
        """
        Check if a metric name exists in a namespace.

        Args:
            namespace: The namespace identifier
            metric_name: The metric name to check

        Returns:
            True if metric name exists in namespace, False otherwise
        """
        key = self._get_key(namespace)
        return bool(self.redis_client.sismember(key, metric_name))
