"""Unit tests for LogsClient operations with mocked dependencies."""

from unittest.mock import Mock, AsyncMock, patch
import pytest

from codd_lib import CoddClient, CoddConfig
from codd_engine.logs.log_patterns import LogPattern
from codd_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from codd_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult,
)


@pytest.fixture
def mock_config():
    """Create a mock CoddConfig."""
    return CoddConfig(
        loki={"base_url": "http://test-loki:3100"},
        splunk={"base_url": "http://test-splunk:8089"},
    )


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


@pytest.mark.asyncio
async def test_logql_generation_with_mocked_query_generator(mock_config):
    """
    Test LogQL query generation with mocked validator.

    Verifies that construct_logql_query returns expected structure
    without making actual LLM calls.
    """
    # Arrange: Create client with mocked LogQL query generator
    with patch(
        "codd_lib.client.provider.logql_module.LogQLModule.get_logql_query_generator"
    ) as mock_get_generator:
        mock_generator = Mock()
        mock_generator.generate_query = AsyncMock(
            return_value=QueryGenerationResult(
                success=True,
                query='{service="payments"} |= "error" | level="error"',
                error=None,
            )
        )
        mock_get_generator.return_value = mock_generator

        client = CoddClient(mock_config)

        # Arrange: Create LogQueryIntent
        patterns = [
            LogPattern(pattern="error", level="error"),
            LogPattern(pattern="exception", level="error"),
            LogPattern(pattern="timeout", level="warn"),
        ]

        intent = LogQueryIntent(
            description="Find error and timeout logs in the payments service",
            backend="loki",
            service="payments",
            patterns=patterns,
            namespace="production",
            default_level="error",
            limit=200,
        )

        # Act: Generate LogQL query
        result = await client.logs.logql.construct_logql_query(intent)

        # Assert: Verify generation was called correctly
        mock_generator.generate_query.assert_called_once_with(intent)

        # Assert: Verify result structure
        assert result.success is True
        assert result.query is not None
        assert len(result.query) > 0
        assert "{" in result.query and "}" in result.query
        assert "service" in result.query or "payments" in result.query
        assert result.error is None


@pytest.mark.asyncio
async def test_splunk_spl_generation_with_mocked_generator(mock_config):
    """
    Test Splunk SPL query generation with mocked validator.

    Verifies that construct_spl_query returns expected structure
    without making actual LLM calls.
    """
    # Arrange: Create client with mocked Splunk query generator
    with patch(
        "codd_lib.client.provider.splunk_module.SplunkModule.get_spl_query_generator"
    ) as mock_get_generator:
        mock_generator = Mock()
        mock_generator.generate_query = AsyncMock(
            return_value=QueryGenerationResult(
                success=True,
                query='search service="api-gateway" (timeout OR "connection refused") | head 200',
                error=None,
            )
        )
        mock_get_generator.return_value = mock_generator

        client = CoddClient(mock_config)

        # Arrange: Create LogQueryIntent for Splunk
        patterns = [
            LogPattern(pattern="timeout", level="warn"),
            LogPattern(pattern="connection refused", level="error"),
        ]

        intent = LogQueryIntent(
            description="Search for timeout and connection errors in the API gateway",
            backend="splunk",
            service="api-gateway",
            patterns=patterns,
            default_level="warn",
            limit=200,
        )

        # Act: Generate Splunk SPL query
        result = await client.logs.splunk.construct_spl_query(intent)

        # Assert: Verify generation was called correctly
        mock_generator.generate_query.assert_called_once_with(intent)

        # Assert: Verify result structure
        assert result.success is True
        assert result.query is not None
        assert len(result.query) > 0
        assert (
            "search" in result.query.lower()
            or "index=" in result.query.lower()
            or "|" in result.query
        )
        assert "api-gateway" in result.query or "api_gateway" in result.query
        assert result.error is None
