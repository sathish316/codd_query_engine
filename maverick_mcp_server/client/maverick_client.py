"""Main Maverick client composing all observability operations."""

from maverick_mcp_server.config import MaverickConfig
from maverick_mcp_server.client.metrics_client import MetricsClient
from maverick_mcp_server.client.logs_client import LogsClient


class MaverickClient:
    """
    Main Maverick client for observability operations.

    Composes:
    - MetricsClient for metrics query generation and semantic search
    - LogsClient for log query generation
    """

    def __init__(self, config: MaverickConfig):
        """
        Initialize the Maverick client.

        Args:
            config: MaverickConfig instance
        """
        self.config = config
        self.metrics = MetricsClient(config)
        self.logs = LogsClient(config)
