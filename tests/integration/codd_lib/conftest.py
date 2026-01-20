"""Fixtures for codd_lib integration tests."""

import pytest
from codd_lib import CoddClient, CoddConfig


@pytest.fixture
def test_namespace():
    """Return test namespace for metrics/logs operations."""
    return "test-namespace"


@pytest.fixture
def codd_client():
    """
    Create a CoddClient instance for testing.

    Uses default configuration which points to:
    - Prometheus at http://host.docker.internal:9090
    - Loki at http://host.docker.internal:3100
    - Redis at localhost:6380
    - ChromaDB (default location)
    """
    config = CoddConfig()
    return CoddClient(config)


@pytest.fixture
def setup_test_metrics_data(codd_client):
    """
    Set up test metrics data in the metadata stores.

    This fixture seeds:
    - Redis metadata store with test metric definitions
    - ChromaDB semantic store with test metric embeddings

    Returns the client after seeding data.
    """
    # For now, this is a no-op fixture
    # In a real implementation, you would seed test data here
    # For example:
    # - Add test metrics to Redis
    # - Add test metrics to ChromaDB with embeddings
    yield codd_client

    # Cleanup after test (if needed)
    # For example:
    # - Remove test data from Redis
    # - Remove test data from ChromaDB
