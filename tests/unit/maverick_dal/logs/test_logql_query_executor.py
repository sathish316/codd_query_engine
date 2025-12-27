"""
Unit tests for LogQLQueryExecutor.

Tests cover:
- Configuration validation
- Query execution (mocked HTTP responses)
- Error handling
- Label metadata retrieval
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from maverick_dal.logs.logql_query_executor import (
    LogQLQueryExecutor,
    LokiConfig,
    QueryResult,
)


@pytest.fixture
def loki_config():
    """Provide a basic Loki configuration."""
    return LokiConfig(base_url="http://localhost:3100")


@pytest.fixture
def loki_config_with_auth():
    """Provide a Loki configuration with authentication."""
    return LokiConfig(
        base_url="http://localhost:3100", auth_token="test-token", org_id="test-org"
    )


@pytest.fixture
def mock_client():
    """Provide a mock HTTP client."""
    client = Mock()
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "status": "success",
        "data": {"resultType": "streams", "result": []},
        "stats": {},
    }
    client.get.return_value = response
    return client


class TestLokiConfig:
    """Test suite for LokiConfig."""

    def test_config_basic(self):
        """Test basic configuration."""
        config = LokiConfig(base_url="http://localhost:3100")
        assert config.base_url == "http://localhost:3100"
        assert config.timeout == 30
        assert config.auth_token is None
        assert config.org_id is None

    def test_config_with_auth(self):
        """Test configuration with authentication."""
        config = LokiConfig(
            base_url="http://localhost:3100",
            timeout=60,
            auth_token="my-token",
            org_id="my-org",
        )
        assert config.base_url == "http://localhost:3100"
        assert config.timeout == 60
        assert config.auth_token == "my-token"
        assert config.org_id == "my-org"

    def test_config_strips_trailing_slash(self):
        """Test that trailing slashes are removed from base_url."""
        config = LokiConfig(base_url="http://localhost:3100/")
        assert config.base_url == "http://localhost:3100"

        config = LokiConfig(base_url="http://localhost:3100///")
        assert config.base_url == "http://localhost:3100"

    def test_config_empty_base_url_raises_error(self):
        """Test that empty base_url raises ValueError."""
        with pytest.raises(ValueError, match="base_url cannot be empty"):
            LokiConfig(base_url="")


class TestLogQLQueryExecutor:
    """Test suite for LogQLQueryExecutor."""

    def test_executor_initialization(self, loki_config, mock_client):
        """Test executor initialization."""
        executor = LogQLQueryExecutor(loki_config, client=mock_client)
        assert executor.config == loki_config
        assert executor._client == mock_client

    def test_build_headers_basic(self, loki_config, mock_client):
        """Test header building without auth."""
        executor = LogQLQueryExecutor(loki_config, client=mock_client)
        headers = executor._build_headers()

        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers
        assert "X-Scope-OrgID" not in headers

    def test_build_headers_with_auth(self, loki_config_with_auth, mock_client):
        """Test header building with authentication."""
        executor = LogQLQueryExecutor(loki_config_with_auth, client=mock_client)
        headers = executor._build_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["X-Scope-OrgID"] == "test-org"

    def test_query_range_default_time(self, loki_config, mock_client):
        """Test range query with default time range."""
        executor = LogQLQueryExecutor(loki_config, client=mock_client)

        result = executor.query_range(query='{job="varlogs"}')

        assert result.status == "success"
        assert mock_client.get.called
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://localhost:3100/loki/api/v1/query_range"
        assert "query" in call_args[1]["params"]
        assert call_args[1]["params"]["query"] == '{job="varlogs"}'

    def test_query_range_custom_time(self, loki_config, mock_client):
        """Test range query with custom time range."""
        executor = LogQLQueryExecutor(loki_config, client=mock_client)

        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 1, 0, 0)

        result = executor.query_range(
            query='{job="api"}', start=start, end=end, limit=500, direction="forward"
        )

        assert result.status == "success"
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["limit"] == 500
        assert params["direction"] == "forward"
        assert params["start"] == int(start.timestamp() * 1e9)
        assert params["end"] == int(end.timestamp() * 1e9)

    def test_query_range_with_step(self, loki_config, mock_client):
        """Test range query with step parameter."""
        executor = LogQLQueryExecutor(loki_config, client=mock_client)

        result = executor.query_range(query='rate({job="api"}[5m])', step=60)

        assert result.status == "success"
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["step"] == 60

    def test_get_labels(self, loki_config, mock_client):
        """Test getting all labels."""
        mock_client.get.return_value.json.return_value = {
            "status": "success",
            "data": ["job", "level", "instance"],
        }

        executor = LogQLQueryExecutor(loki_config, client=mock_client)
        result = executor.get_labels()

        assert result.status == "success"
        assert result.data == ["job", "level", "instance"]
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://localhost:3100/loki/api/v1/labels"

    def test_get_label_values(self, loki_config, mock_client):
        """Test getting values for a specific label."""
        mock_client.get.return_value.json.return_value = {
            "status": "success",
            "data": ["api", "frontend", "backend"],
        }

        executor = LogQLQueryExecutor(loki_config, client=mock_client)
        result = executor.get_label_values("job")

        assert result.status == "success"
        assert result.data == ["api", "frontend", "backend"]
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "http://localhost:3100/loki/api/v1/label/job/values"

    def test_get_label_values_with_query(self, loki_config, mock_client):
        """Test getting label values filtered by query."""
        mock_client.get.return_value.json.return_value = {
            "status": "success",
            "data": ["error", "warn"],
        }

        executor = LogQLQueryExecutor(loki_config, client=mock_client)
        result = executor.get_label_values("level", query='{job="api"}')

        assert result.status == "success"
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["query"] == '{job="api"}'

    def test_query_error_handling(self, loki_config, mock_client):
        """Test error handling for failed queries."""
        mock_client.get.side_effect = Exception("Connection failed")

        executor = LogQLQueryExecutor(loki_config, client=mock_client)
        result = executor.query_range(query='{job="test"}')

        assert result.status == "error"
        assert result.error is not None
        assert "Connection failed" in result.error

    def test_close_method(self, loki_config, mock_client):
        """Test close method."""
        executor = LogQLQueryExecutor(loki_config, client=mock_client)
        executor.close()

        assert mock_client.close.called


class TestQueryResult:
    """Test suite for QueryResult."""

    def test_query_result_success(self):
        """Test successful query result."""
        result = QueryResult(
            status="success",
            data={"resultType": "streams", "result": []},
            stats={"summary": {}},
        )

        assert result.status == "success"
        assert result.data is not None
        assert result.error is None
        assert result.stats is not None

    def test_query_result_error(self):
        """Test error query result."""
        result = QueryResult(status="error", error="Query failed: invalid syntax")

        assert result.status == "error"
        assert result.error == "Query failed: invalid syntax"
        assert result.data is None
        assert result.stats is None
