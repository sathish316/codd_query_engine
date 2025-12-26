"""
LogQL query executor for Loki API integration.

This module provides direct query execution against Grafana Loki using the HTTP API.
Supports both log queries (streaming) and metric queries (instant/range).
"""

from typing import Optional, Any, Literal
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin
import json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class LogQLExecutionError(Exception):
    """Exception raised when LogQL query execution fails."""
    pass


@dataclass
class LokiConfig:
    """
    Configuration for Loki connection.

    Attributes:
        base_url: Base URL of the Loki instance (e.g., "http://localhost:3100")
        timeout: Request timeout in seconds (default: 30)
        auth_token: Optional Bearer token for authentication
        org_id: Optional X-Scope-OrgID header for multi-tenancy
    """
    base_url: str
    timeout: int = 30
    auth_token: Optional[str] = None
    org_id: Optional[str] = None

    def __post_init__(self):
        """Validate configuration."""
        if not self.base_url:
            raise ValueError("base_url cannot be empty")

        # Ensure base_url ends without trailing slash for proper URL joining
        self.base_url = self.base_url.rstrip('/')


@dataclass
class QueryResult:
    """
    Result of a LogQL query execution.

    Attributes:
        status: Status of the query ("success" or "error")
        data: Response data from Loki
        error: Error message if query failed
        stats: Query execution statistics
    """
    status: str
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    stats: Optional[dict[str, Any]] = None


class LogQLQueryExecutor:
    """
    Client for executing LogQL queries against Grafana Loki.

    Supports both log queries (streaming) and metric queries (instant/range).
    Uses the Loki HTTP API for query execution.

    Args:
        config: LokiConfig instance with connection settings
        client: Optional httpx.Client for custom configuration
    """

    def __init__(self, config: LokiConfig, client: Optional[Any] = None):
        """
        Initialize LogQL query executor.

        Args:
            config: LokiConfig instance with connection settings
            client: Optional httpx.Client instance (for testing or custom config)

        Raises:
            ImportError: If httpx is not installed
        """
        if not HTTPX_AVAILABLE and client is None:
            raise ImportError(
                "httpx is required for LogQLQueryExecutor. "
                "Install with: pip install httpx"
            )

        self.config = config
        self._client = client

    @property
    def client(self) -> Any:
        """Get or create the HTTP client."""
        if self._client is None:
            import httpx
            self._client = httpx.Client(
                timeout=self.config.timeout,
                headers=self._build_headers()
            )
        return self._client

    def _build_headers(self) -> dict[str, str]:
        """
        Build HTTP headers for Loki requests.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {"Content-Type": "application/json"}

        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"

        if self.config.org_id:
            headers["X-Scope-OrgID"] = self.config.org_id

        return headers

    def query_range(
        self,
        query: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        direction: Literal["backward", "forward"] = "backward",
        step: Optional[int] = None,
    ) -> QueryResult:
        """
        Execute a LogQL range query.

        Queries log data over a time range. Useful for both log streaming
        and metric queries over time ranges.

        Args:
            query: LogQL query string
            start: Start time for the query (default: 1 hour ago)
            end: End time for the query (default: now)
            limit: Maximum number of entries to return (default: 100)
            direction: Query direction - "backward" or "forward" (default: "backward")
            step: Query resolution step in seconds (for metric queries)

        Returns:
            QueryResult with query response data

        Raises:
            LogQLExecutionError: If query execution fails
        """
        # Set default time range if not provided
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(hours=1)

        # Build query parameters
        params = {
            "query": query,
            "start": int(start.timestamp() * 1e9),  # Nanoseconds
            "end": int(end.timestamp() * 1e9),
            "limit": limit,
            "direction": direction,
        }

        if step is not None:
            params["step"] = step

        # Execute query
        url = urljoin(self.config.base_url, "/loki/api/v1/query_range")

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()

            result_data = response.json()

            return QueryResult(
                status=result_data.get("status", "unknown"),
                data=result_data.get("data"),
                stats=result_data.get("stats"),
            )

        except Exception as e:
            logger.error(f"LogQL range query failed: {e}", exc_info=True)
            return QueryResult(
                status="error",
                error=str(e)
            )

    def query_instant(
        self,
        query: str,
        time: Optional[datetime] = None,
        limit: int = 100,
        direction: Literal["backward", "forward"] = "backward",
    ) -> QueryResult:
        """
        Execute a LogQL instant query.

        Queries log data at a single point in time.

        Args:
            query: LogQL query string
            time: Time for the query (default: now)
            limit: Maximum number of entries to return (default: 100)
            direction: Query direction - "backward" or "forward" (default: "backward")

        Returns:
            QueryResult with query response data

        Raises:
            LogQLExecutionError: If query execution fails
        """
        # Set default time if not provided
        if time is None:
            time = datetime.now()

        # Build query parameters
        params = {
            "query": query,
            "time": int(time.timestamp() * 1e9),  # Nanoseconds
            "limit": limit,
            "direction": direction,
        }

        # Execute query
        url = urljoin(self.config.base_url, "/loki/api/v1/query")

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()

            result_data = response.json()

            return QueryResult(
                status=result_data.get("status", "unknown"),
                data=result_data.get("data"),
                stats=result_data.get("stats"),
            )

        except Exception as e:
            logger.error(f"LogQL instant query failed: {e}", exc_info=True)
            return QueryResult(
                status="error",
                error=str(e)
            )

    def get_labels(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> QueryResult:
        """
        Retrieve all label names from Loki.

        Args:
            start: Start time for label query (default: 1 hour ago)
            end: End time for label query (default: now)

        Returns:
            QueryResult with list of label names

        Raises:
            LogQLExecutionError: If query execution fails
        """
        # Set default time range if not provided
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(hours=1)

        params = {
            "start": int(start.timestamp() * 1e9),
            "end": int(end.timestamp() * 1e9),
        }

        url = urljoin(self.config.base_url, "/loki/api/v1/labels")

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()

            result_data = response.json()

            return QueryResult(
                status=result_data.get("status", "unknown"),
                data=result_data.get("data"),
            )

        except Exception as e:
            logger.error(f"Failed to retrieve labels: {e}", exc_info=True)
            return QueryResult(
                status="error",
                error=str(e)
            )

    def get_label_values(
        self,
        label_name: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        query: Optional[str] = None,
    ) -> QueryResult:
        """
        Retrieve all values for a specific label from Loki.

        Args:
            label_name: Name of the label
            start: Start time for label query (default: 1 hour ago)
            end: End time for label query (default: now)
            query: Optional LogQL query to filter label values

        Returns:
            QueryResult with list of label values

        Raises:
            LogQLExecutionError: If query execution fails
        """
        # Set default time range if not provided
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(hours=1)

        params = {
            "start": int(start.timestamp() * 1e9),
            "end": int(end.timestamp() * 1e9),
        }

        if query:
            params["query"] = query

        url = urljoin(self.config.base_url, f"/loki/api/v1/label/{label_name}/values")

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()

            result_data = response.json()

            return QueryResult(
                status=result_data.get("status", "unknown"),
                data=result_data.get("data"),
            )

        except Exception as e:
            logger.error(f"Failed to retrieve label values for '{label_name}': {e}", exc_info=True)
            return QueryResult(
                status="error",
                error=str(e)
            )

    def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
