"""Lean client for Splunk SPL operations - query generation."""

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult,
)

from maverick_lib.config import MaverickConfig
from maverick_lib.client.provider import LogsModule, SplunkModule
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


class LogsSplunkClient:
    """
    Lean client for Splunk SPL operations.

    Provides:
    - Splunk SPL query generation from intent
    """

    def __init__(
        self,
        config: MaverickConfig,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the Splunk SPL client.

        Args:
            config: MaverickConfig instance
        """
        self.config = config

        # Opus components
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager

        # Log query validator (shared across all log backends)
        self.log_query_validator = LogsModule.get_log_query_validator(config_manager)

        # Query generator will be created lazily when needed
        self._spl_query_generator = None

    @property
    def spl_query_generator(self):
        """Lazily initialize and return the Splunk SPL query generator."""
        if self._spl_query_generator is None:
            self._spl_query_generator = SplunkModule.get_spl_query_generator(
                self.config_manager,
                self.instructions_manager,
                self.log_query_validator,
            )
        return self._spl_query_generator

    async def construct_spl_query(self, intent: LogQueryIntent) -> QueryGenerationResult:
        """
        Generate a valid Splunk SPL query from log query intent.

        Args:
            intent: LogQueryIntent with query requirements

        Returns:
            QueryGenerationResult with final query and metadata
        """
        result = await self.spl_query_generator.generate_query(intent)
        return result

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
