"""Logs client for log query operations."""

from maverick_mcp_server.config import MaverickConfig
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager
from maverick_mcp_server.client.logs_logql_client import LogsLogQLClient
from maverick_mcp_server.client.logs_splunk_client import LogsSplunkClient


class LogsClient:
    """
    Client for logs operations.

    Provides:
    - LogQL query generation for Loki
    - Splunk SPL query generation
    """

    def __init__(
        self,
        config: MaverickConfig,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the logs client.

        Args:
            config: MaverickConfig instance
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance
        """
        self.config = config
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager
        self.logql = LogsLogQLClient(config, config_manager, instructions_manager)
        self.splunk = LogsSplunkClient(config, config_manager, instructions_manager)
