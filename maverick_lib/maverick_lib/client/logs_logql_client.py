"""Client for LogQL operations - query generation."""

from maverick_lib.config import MaverickConfig
from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult,
)
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

from maverick_lib.client.provider import LogsModule, LogQLModule


class LogsLogQLClient:
    """
    Lean client for LogQL operations.

    Provides:
    - LogQL query generation from intent
    - Query execution against Loki
    - Label and label values retrieval
    """

    def __init__(
        self,
        config: MaverickConfig,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the LogQL client.

        Args:
            config: MaverickConfig instance
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance
        """
        self.config = config

        # Opus components
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager

        # LogQL validator (shared across all log backends)
        self.log_query_validator = LogsModule.get_log_query_validator()

        # LogQL Query generator
        self._logql_query_generator = None

    @property
    def logql_query_generator(self):
        """Lazily initialize and return the LogQL query generator."""
        if self._logql_query_generator is None:
            self._logql_query_generator = LogQLModule.get_logql_query_generator(
                self.config_manager,
                self.instructions_manager,
                self.log_query_validator,
            )
        return self._logql_query_generator

    async def construct_logql_query(self, intent: LogQueryIntent) -> QueryGenerationResult:
        """
        Generate a valid LogQL query from log query intent.

        Args:
            intent: LogQueryIntent with query requirements

        Returns:
            QueryGenerationResult with final query and metadata
        """
        result = await self.logql_query_generator.generate_query(intent)
        return result

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
