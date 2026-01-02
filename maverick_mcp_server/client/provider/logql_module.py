"""Dependency injection module for LogQL operations (Spring-like pattern)."""

from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

from maverick_dal.logs.logql_query_executor import LogQLQueryExecutor, LokiConfig
from maverick_engine.validation_engine.logs.log_query_validator import LogQueryValidator
from maverick_engine.querygen_engine.agent.logs.logql_query_generator_agent import (
    LogQLQueryGeneratorAgent,
)
from maverick_mcp_server.config import MaverickConfig


class LogQLModule:
    """Module for LogQL operations - provides configured dependencies."""

    @classmethod
    def get_logql_query_executor(cls, config: MaverickConfig) -> LogQLQueryExecutor:
        """
        Provide a configured LogQLQueryExecutor instance.

        Args:
            config: MaverickConfig with Loki configuration

        Returns:
            LogQLQueryExecutor instance
        """
        loki_config = LokiConfig(
            base_url=config.loki.base_url,
            timeout=config.loki.timeout,
        )
        return LogQLQueryExecutor(loki_config)

    @classmethod
    def get_logql_query_generator(
        cls,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
        log_query_validator: LogQueryValidator,
    ) -> LogQLQueryGeneratorAgent:
        """
        Provide a LogQLQueryGeneratorAgent instance.

        Args:
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance
            log_query_validator: LogQueryValidator instance

        Returns:
            LogQLQueryGeneratorAgent instance
        """
        return LogQLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            log_query_validator=log_query_validator,
        )
