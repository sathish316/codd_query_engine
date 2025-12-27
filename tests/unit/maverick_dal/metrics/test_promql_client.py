"""
Tests for PromQL client.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from maverick_dal.metrics.promql_client import PromQLClient


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx.Client."""
    with patch("maverick_dal.metrics.promql_client.httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def promql_client(mock_httpx_client):
    """Create PromQL client with mocked HTTP client."""
    return PromQLClient("http://localhost:9090")


class TestPromQLClient:
    """Test client initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        client = PromQLClient("http://localhost:9090")
        assert client.base_url == "http://localhost:9090"
        assert client.timeout == 30.0
        assert client.headers == {}

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        headers = {"Authorization": "Bearer token123"}
        client = PromQLClient("http://prometheus:9090", timeout=60.0, headers=headers)
        assert client.base_url == "http://prometheus:9090"
        assert client.timeout == 60.0
        assert client.headers == headers

    def test_context_manager(self, mock_httpx_client):
        """Test context manager protocol."""
        with PromQLClient("http://localhost:9090") as client:
            assert client is not None
        mock_httpx_client.close.assert_called_once()

    def test_get_label_names_success(self, promql_client, mock_httpx_client):
        """Test getting label names."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": ["__name__", "job", "instance"],
        }
        mock_httpx_client.request.return_value = mock_response

        result = promql_client.get_label_names()

        assert result == ["__name__", "job", "instance"]
        mock_httpx_client.request.assert_called_once_with(
            "GET", "http://localhost:9090/api/v1/labels", params={}
        )

    def test_get_label_values_success(self, promql_client, mock_httpx_client):
        """Test getting label values."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": ["prometheus", "node-exporter"],
        }
        mock_httpx_client.request.return_value = mock_response

        result = promql_client.get_label_values("job")

        assert result == ["prometheus", "node-exporter"]
        mock_httpx_client.request.assert_called_once_with(
            "GET", "http://localhost:9090/api/v1/label/job/values", params={}
        )

    def test_get_series_success(self, promql_client, mock_httpx_client):
        """Test getting series."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": [
                {"__name__": "up", "job": "prometheus", "instance": "localhost:9090"},
                {"__name__": "up", "job": "node", "instance": "localhost:9100"},
            ],
        }
        mock_httpx_client.request.return_value = mock_response

        result = promql_client.get_series(match=["up"])

        assert len(result) == 2
        assert result[0]["job"] == "prometheus"
        assert result[1]["job"] == "node"

    def test_get_series_with_time_range(self, promql_client, mock_httpx_client):
        """Test getting series with time range."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 2, 0, 0, 0)

        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": [{"__name__": "up"}],
        }
        mock_httpx_client.request.return_value = mock_response

        promql_client.get_series(match=["up"], start=start, end=end)

        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["params"]["start"] == start.timestamp()
        assert call_args[1]["params"]["end"] == end.timestamp()

    def test_get_metric_metadata_success(self, promql_client, mock_httpx_client):
        """Test getting metric metadata."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {"up": [{"type": "gauge", "help": "Up status", "unit": ""}]},
        }
        mock_httpx_client.request.return_value = mock_response

        result = promql_client.get_metric_metadata()

        assert "up" in result
        assert result["up"][0]["type"] == "gauge"

    def test_query_instant_success(self, promql_client, mock_httpx_client):
        """Test instant query execution."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {"__name__": "up", "job": "prometheus"},
                        "value": [1704067200, "1"],
                    }
                ],
            },
        }
        mock_httpx_client.request.return_value = mock_response

        result = promql_client.query_instant("up")

        assert result["resultType"] == "vector"
        assert len(result["result"]) == 1
        mock_httpx_client.request.assert_called_once_with(
            "POST", "http://localhost:9090/api/v1/query", params={"query": "up"}
        )

    def test_query_instant_with_time(self, promql_client, mock_httpx_client):
        """Test instant query with custom time."""
        query_time = datetime(2024, 1, 1, 12, 0, 0)

        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {"resultType": "vector", "result": []},
        }
        mock_httpx_client.request.return_value = mock_response

        promql_client.query_instant("up", time=query_time)

        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["params"]["time"] == query_time.timestamp()

    def test_query_range_success(self, promql_client, mock_httpx_client):
        """Test range query execution."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 1, 0, 0)

        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {"__name__": "up"},
                        "values": [[1704067200, "1"], [1704067260, "1"]],
                    }
                ],
            },
        }
        mock_httpx_client.request.return_value = mock_response

        result = promql_client.query_range("up", start, end, "1m")

        assert result["resultType"] == "matrix"
        assert len(result["result"]) == 1
        call_args = mock_httpx_client.request.call_args
        assert call_args[1]["params"]["start"] == start.timestamp()
        assert call_args[1]["params"]["end"] == end.timestamp()
        assert call_args[1]["params"]["step"] == "1m"

    def test_health_check_success(self, promql_client, mock_httpx_client):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_httpx_client.get.return_value = mock_response

        result = promql_client.health_check()

        assert result is True
        mock_httpx_client.get.assert_called_once_with("http://localhost:9090/-/healthy")

    def test_health_check_failure(self, promql_client, mock_httpx_client):
        """Test failed health check."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_httpx_client.get.return_value = mock_response

        result = promql_client.health_check()

        assert result is False
