"""Main Codd client composing all observability operations."""

from typing import Optional

from codd_lib.config import CoddConfig
from codd_lib.client.metrics_client import MetricsClient
from codd_lib.client.logs_client import LogsClient
from codd_lib.client.provider import OpusModule


class CoddClient:
    """
    Main Codd client for observability operations.

    Composes:
    - MetricsClient for metrics query generation and semantic search
    - LogsClient for log query generation
    """

    def __init__(self, config: CoddConfig):
        """
        Initialize the Codd client.

        Args:
            config: CoddConfig instance
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
