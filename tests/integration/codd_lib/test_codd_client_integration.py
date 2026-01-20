"""Integration tests for CoddClient."""

import pytest
from codd_lib import CoddClient, CoddConfig


@pytest.mark.integration
def test_codd_client_initialization():
    """Test CoddClient can be initialized and configured end-to-end."""
    # Create custom config
    config = CoddConfig(
        config_path="~/.codd/config.yml",
        prometheus={"base_url": "http://test-prometheus:9090"},
        loki={"base_url": "http://test-loki:3100"},
    )

    # Initialize client
    client = CoddClient(config)

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
def test_codd_client_opus_components():
    """Test CoddClient Opus components are properly initialized."""
    config = CoddConfig()
    client = CoddClient(config)

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
