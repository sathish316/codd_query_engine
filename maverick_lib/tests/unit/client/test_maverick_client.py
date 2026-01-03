"""Unit tests for MaverickClient."""

from maverick_lib import MaverickClient, MaverickConfig


def test_maverick_client_initialization():
    """Test MaverickClient initializes with config."""
    config = MaverickConfig()
    client = MaverickClient(config)

    assert client.config == config
    assert client.config_manager is not None
    assert client.instructions_manager is not None
    assert client.metrics is not None
    assert client.logs is not None


def test_maverick_client_has_metrics_client():
    """Test MaverickClient has metrics client."""
    config = MaverickConfig()
    client = MaverickClient(config)

    assert hasattr(client.metrics, "search_relevant_metrics")
    assert hasattr(client.metrics, "construct_promql_query")
    assert hasattr(client.metrics, "promql")


def test_maverick_client_has_logs_client():
    """Test MaverickClient has logs client."""
    config = MaverickConfig()
    client = MaverickClient(config)

    assert hasattr(client.logs, "logql")
    assert hasattr(client.logs, "splunk")
    assert hasattr(client.logs.logql, "construct_logql_query")
    assert hasattr(client.logs.splunk, "construct_spl_query")
