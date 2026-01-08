"""Unit tests for MaverickClient."""

from unittest.mock import Mock, patch

import pytest

from maverick_lib import MaverickClient, MaverickConfig


@pytest.fixture(autouse=True)
def mock_chromadb_connection():
    """Prevent real ChromaDB connections during MaverickClient initialization."""
    with patch(
        "maverick_lib.client.metrics_promql_client.PromQLModule.get_semantic_store"
    ) as mock_get_store:
        mock_store = Mock()
        mock_store.search_metadata.return_value = []
        mock_get_store.return_value = mock_store
        yield


def test_maverick_client_initialization():
    """Test MaverickClient initializes with config."""
    config = MaverickConfig()
    client = MaverickClient(config)

    assert client.config == config
    assert client.config_manager is not None
    assert client.instructions_manager is not None
    assert client.metrics is not None
    assert client.logs is not None
