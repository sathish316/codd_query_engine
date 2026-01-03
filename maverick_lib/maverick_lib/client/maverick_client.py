"""Main Maverick client composing all observability operations."""

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

        self.metrics = MetricsClient(
            config, self.config_manager, self.instructions_manager
        )
        self.logs = LogsClient(config, self.config_manager, self.instructions_manager)
