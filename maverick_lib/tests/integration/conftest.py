"""Shared fixtures for maverick_lib integration tests."""

import os
import pytest
import redis
import chromadb

from maverick_lib.client import MaverickClient
from maverick_lib.config import MaverickConfig
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


@pytest.fixture(scope="session")
def config_manager():
    """Initialize ConfigManager for integration tests using ~/.maverick_test config."""
    config_dir = expand_path("$HOME/.maverick_test")
    return ConfigManager(config_dir, "config.yml")


@pytest.fixture(scope="session")
def instructions_manager():
    """Initialize InstructionsManager for integration tests."""
    return InstructionsManager()


@pytest.fixture(scope="session")
def redis_client():
    """
    Create Redis client for integration tests.

    Uses test Redis instance on port 6380.
    Set REDIS_TEST_PORT environment variable to override.
    """
    redis_port = int(os.getenv("REDIS_TEST_PORT", "6380"))
    redis_host = os.getenv("REDIS_TEST_HOST", "localhost")

    client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    # Verify Redis is available
    try:
        client.ping()
    except redis.ConnectionError:
        pytest.skip(f"Redis is not available at {redis_host}:{redis_port}")

    return client


@pytest.fixture(scope="session")
def chromadb_client():
    """
    Create ChromaDB client for integration tests.

    Uses ChromaDB instance on port 8000.
    Set CHROMADB_HOST and CHROMADB_PORT environment variables to override.
    """
    chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
    chromadb_port = int(os.getenv("CHROMADB_PORT", "8000"))

    try:
        client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port)
        # Test connection
        client.heartbeat()
    except Exception:
        pytest.skip(f"ChromaDB is not available at {chromadb_host}:{chromadb_port}")

    return client


@pytest.fixture(scope="session")
def maverick_config():
    """
    Create test configuration for MaverickClient.

    Uses ~/.maverick_test/config.yml and test service ports.
    """
    return MaverickConfig(
        config_path="~/.maverick_test/config.yml",
        prometheus={
            "base_url": os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
            "timeout": 30.0,
        },
        loki={
            "base_url": os.getenv("LOKI_URL", "http://localhost:3100"),
            "timeout": 30.0,
        },
        redis={
            "host": os.getenv("REDIS_TEST_HOST", "localhost"),
            "port": int(os.getenv("REDIS_TEST_PORT", "6380")),
            "db": 0,
        },
        semantic_store={
            "chromadb_host": os.getenv("CHROMADB_HOST", "localhost"),
            "chromadb_port": int(os.getenv("CHROMADB_PORT", "8000")),
            "collection_name": "metrics_semantic_metadata",
        },
    )


@pytest.fixture
def maverick_client(maverick_config):
    """
    Create MaverickClient instance for integration tests.

    Returns a real MaverickClient that will:
    - Use real semantic store (ChromaDB)
    - Use real query generators (with LLM calls)
    - Use real validators (with LLM calls)
    """
    client = MaverickClient(maverick_config)
    return client


@pytest.fixture
def test_namespace():
    """Provide a test namespace for metrics and logs."""
    return "test:api_service"


@pytest.fixture
def setup_test_metrics_data(maverick_client, redis_client, test_namespace):
    """
    Seed test metrics in Redis metadata store.

    This fixture prepares the metadata store with known metric names
    that tests can use for query generation.
    """
    # Seed Redis with metric names
    metric_names = {
        "http_requests_total",
        "http_request_duration_seconds",
        "http_request_duration_seconds_bucket",
        "http_request_duration_seconds_sum",
        "http_request_duration_seconds_count",
        "cpu_usage_percent",
        "memory_usage_bytes",
    }

    # Use the metadata store from the PromQL client
    metadata_store = maverick_client.metrics.promql.metrics_metadata_store
    metadata_store.set_metric_names(test_namespace, metric_names)

    yield test_namespace

    # Cleanup after test
    redis_client.delete(f"metrics:names:{test_namespace}")
