"""Integration tests for MaverickClient."""

import pytest
from maverick_lib import MaverickClient, MaverickConfig


@pytest.mark.integration
def test_maverick_client_initialization():
    """Test MaverickClient can be initialized and configured end-to-end."""
    # Create custom config
    config = MaverickConfig(
        config_path="~/.maverick/config.yml",
        prometheus={"base_url": "http://test-prometheus:9090"},
        loki={"base_url": "http://test-loki:3100"},
    )

    # Initialize client
    client = MaverickClient(config)

    # Verify client structure
    assert client.config.prometheus.base_url == "http://test-prometheus:9090"
    assert client.config.loki.base_url == "http://test-loki:3100"

    # Verify sub-clients are accessible
    assert client.metrics is not None
    assert client.metrics.promql is not None
    assert client.logs is not None
    assert client.logs.logql is not None
    assert client.logs.splunk is not None


@pytest.mark.integration
def test_maverick_client_opus_components():
    """Test MaverickClient Opus components are properly initialized."""
    config = MaverickConfig()
    client = MaverickClient(config)

    # Verify Opus components exist at client level
    assert client.config_manager is not None
    assert client.instructions_manager is not None

    # Verify they're passed to metrics client (which exposes them)
    assert client.metrics.config_manager is not None
    assert client.metrics.instructions_manager is not None
    assert client.metrics.config_manager == client.config_manager
    assert client.metrics.instructions_manager == client.instructions_manager

    # Verify they're passed to logs client (which exposes them)
    assert client.logs.config_manager is not None
    assert client.logs.instructions_manager is not None
    assert client.logs.config_manager == client.config_manager
    assert client.logs.instructions_manager == client.instructions_manager
