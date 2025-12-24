"""
PromQL client for Prometheus API.

Supports:
1. Metadata queries (labels, label values, series)
2. Query execution (instant and range queries)
"""

from typing import Any, Optional
from datetime import datetime
import httpx


class PromQLClient:
    """
    Client for querying Prometheus using PromQL.

    Provides methods for metadata retrieval and query execution.

    Args:
        base_url: Prometheus server URL (e.g., "http://localhost:9090")
        timeout: Request timeout in seconds
        headers: Optional custom headers for authentication
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        headers: Optional[dict[str, str]] = None
    ):
        """
        Initialize PromQL client.

        Args:
            base_url: Prometheus server URL
            timeout: Request timeout in seconds
            headers: Optional custom headers
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = headers or {}
        self.client = httpx.Client(timeout=timeout, headers=self.headers)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Make HTTP request to Prometheus API.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPError: On HTTP errors
            ValueError: On API errors
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.client.request(method, url, params=params)
            response.raise_for_status()

            data = response.json()

            # Check for Prometheus API errors
            if data.get("status") != "success":
                error = data.get("error", "Unknown error")
                error_type = data.get("errorType", "unknown")
                raise ValueError(f"Prometheus API error ({error_type}): {error}")

            return data

        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"HTTP error querying Prometheus: {e}") from e

    # Metadata methods

    def get_label_names(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        match: Optional[list[str]] = None
    ) -> list[str]:
        """
        Get list of label names.

        Args:
            start: Start time for filtering (optional)
            end: End time for filtering (optional)
            match: Series selectors to filter by (optional)

        Returns:
            List of label names
        """
        params: dict[str, Any] = {}

        if start:
            params["start"] = start.timestamp()
        if end:
            params["end"] = end.timestamp()
        if match:
            params["match[]"] = match

        data = self._make_request("GET", "/api/v1/labels", params)
        return data.get("data", [])

    def get_label_values(
        self,
        label_name: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        match: Optional[list[str]] = None
    ) -> list[str]:
        """
        Get list of label values for a specific label.

        Args:
            label_name: Name of the label
            start: Start time for filtering (optional)
            end: End time for filtering (optional)
            match: Series selectors to filter by (optional)

        Returns:
            List of label values
        """
        params: dict[str, Any] = {}

        if start:
            params["start"] = start.timestamp()
        if end:
            params["end"] = end.timestamp()
        if match:
            params["match[]"] = match

        endpoint = f"/api/v1/label/{label_name}/values"
        data = self._make_request("GET", endpoint, params)
        return data.get("data", [])

    def get_series(
        self,
        match: list[str],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> list[dict[str, str]]:
        """
        Get list of time series matching selectors.

        Args:
            match: Series selectors (required, e.g., ['up', 'node_cpu_seconds_total'])
            start: Start time for filtering (optional)
            end: End time for filtering (optional)

        Returns:
            List of label sets identifying matching series
        """
        if not match:
            raise ValueError("match parameter is required")

        params: dict[str, Any] = {"match[]": match}

        if start:
            params["start"] = start.timestamp()
        if end:
            params["end"] = end.timestamp()

        data = self._make_request("GET", "/api/v1/series", params)
        return data.get("data", [])

    def get_metric_metadata(
        self,
        metric: Optional[str] = None,
        limit: Optional[int] = None
    ) -> dict[str, list[dict[str, str]]]:
        """
        Get metadata about metrics.

        Args:
            metric: Metric name to filter by (optional)
            limit: Maximum number of metrics to return (optional)

        Returns:
            Dictionary mapping metric names to metadata
        """
        params: dict[str, Any] = {}

        if metric:
            params["metric"] = metric
        if limit:
            params["limit"] = limit

        data = self._make_request("GET", "/api/v1/metadata", params)
        return data.get("data", {})

    # Query methods

    def query_instant(
        self,
        query: str,
        time: Optional[datetime] = None,
        timeout: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Execute instant PromQL query.

        Evaluates the query at a single point in time.

        Args:
            query: PromQL query string
            time: Evaluation timestamp (optional, defaults to current time)
            timeout: Query timeout (optional, e.g., "30s")

        Returns:
            Query result with 'resultType' and 'result' fields
        """
        if not query:
            raise ValueError("query parameter is required")

        params: dict[str, Any] = {"query": query}

        if time:
            params["time"] = time.timestamp()
        if timeout:
            params["timeout"] = timeout

        data = self._make_request("POST", "/api/v1/query", params)
        return data.get("data", {})

    def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str,
        timeout: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Execute range PromQL query.

        Evaluates the query over a time range.

        Args:
            query: PromQL query string
            start: Start timestamp
            end: End timestamp
            step: Query resolution step width (e.g., "15s", "1m", "1h")
            timeout: Query timeout (optional, e.g., "30s")

        Returns:
            Query result with 'resultType' and 'result' fields
        """
        if not query:
            raise ValueError("query parameter is required")
        if not step:
            raise ValueError("step parameter is required")

        params: dict[str, Any] = {
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step
        }

        if timeout:
            params["timeout"] = timeout

        data = self._make_request("POST", "/api/v1/query_range", params)
        return data.get("data", {})

    # Utility methods

    def health_check(self) -> bool:
        """
        Check if Prometheus server is healthy.

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self.client.get(f"{self.base_url}/-/healthy")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def ready_check(self) -> bool:
        """
        Check if Prometheus server is ready.

        Returns:
            True if server is ready, False otherwise
        """
        try:
            response = self.client.get(f"{self.base_url}/-/ready")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
