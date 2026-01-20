"""Dependency injection module for Splunk SPL operations (Spring-like pattern)."""

from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

from codd_engine.validation_engine.logs.log_query_validator import LogQueryValidator
from codd_engine.querygen_engine.agent.logs.spl_query_generator_agent import (
    SplunkSPLQueryGeneratorAgent,
)


class SplunkModule:
    """Module for Splunk SPL operations - provides configured dependencies."""

    @classmethod
    def get_spl_query_generator(
        cls,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
        log_query_validator: LogQueryValidator,
    ) -> SplunkSPLQueryGeneratorAgent:
        """
        Provide a SplunkSPLQueryGeneratorAgent instance.

        Args:
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance
            log_query_validator: LogQueryValidator instance

        Returns:
            SplunkSPLQueryGeneratorAgent instance
        """
        return SplunkSPLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            log_query_validator=log_query_validator,
        )
