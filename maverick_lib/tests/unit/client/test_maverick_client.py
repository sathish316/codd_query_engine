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
