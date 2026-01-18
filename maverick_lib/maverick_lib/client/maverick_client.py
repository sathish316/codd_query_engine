"""Main Maverick client composing all observability operations."""

from typing import Optional

from maverick_lib.config import MaverickConfig
from maverick_lib.client.metrics_client import MetricsClient
from maverick_lib.client.logs_client import LogsClient
from maverick_lib.client.provider import OpusModule


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
        # Opus components
        self.config_manager = OpusModule.get_config_manager(config)
        self.instructions_manager = OpusModule.get_instructions_manager()

        # Lazily initialized clients
        self._metrics: Optional[MetricsClient] = None
        self._logs: Optional[LogsClient] = None

    @property
    def metrics(self) -> MetricsClient:
        """Lazily initialize and return the MetricsClient."""
        if self._metrics is None:
            self._metrics = MetricsClient(
                self.config, self.config_manager, self.instructions_manager
            )
        return self._metrics

    @property
    def logs(self) -> LogsClient:
        """Lazily initialize and return the LogsClient."""
        if self._logs is None:
            self._logs = LogsClient(
                self.config, self.config_manager, self.instructions_manager
            )
        return self._logs
