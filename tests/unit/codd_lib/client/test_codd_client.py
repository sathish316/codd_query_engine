"""Unit tests for CoddClient."""

from unittest.mock import Mock, patch

import pytest

from codd_lib import CoddClient, CoddConfig


@pytest.fixture(autouse=True)
def mock_chromadb_connection():
    """Prevent real ChromaDB connections during CoddClient initialization."""
    with patch(
        "codd_lib.client.metrics_promql_client.PromQLModule.get_semantic_store"
    ) as mock_get_store:
        mock_store = Mock()
        mock_store.search_metadata.return_value = []
        mock_get_store.return_value = mock_store
        yield


def test_codd_client_initialization():
    """Test CoddClient initializes with config."""
    config = CoddConfig()
    client = CoddClient(config)

    assert client.config == config
    assert client.config_manager is not None
    assert client.instructions_manager is not None
    assert client.metrics is not None
    assert client.logs is not None
