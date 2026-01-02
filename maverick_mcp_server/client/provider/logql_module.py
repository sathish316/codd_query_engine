"""Dependency injection module for LogQL operations (Spring-like pattern)."""

from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

from maverick_engine.validation_engine.logs.log_query_validator import LogQueryValidator
from maverick_engine.validation_engine.logs.syntax import (
    LogQLSyntaxValidator,
)
from maverick_engine.querygen_engine.agent.logs.logql_query_generator_agent import (
    LogQLQueryGeneratorAgent,
)


class LogQLModule:
    """Module for LogQL operations - provides configured dependencies."""

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

    @classmethod
    def get_log_query_validator(cls) -> LogQueryValidator:
        """
        Provide a LogQueryValidator instance with syntax validators.

        Returns:
            LogQueryValidator instance with LogQL and Splunk validators
        """
        syntax_validators = {
            "loki": cls._get_logql_syntax_validator(),
            "splunk": cls._get_splunk_syntax_validator(),
        }

        return LogQueryValidator(syntax_validators=syntax_validators)

    @classmethod
    def _get_logql_syntax_validator(cls) -> LogQLSyntaxValidator:
        """
        Provide a LogQLSyntaxValidator instance.

        Returns:
            LogQLSyntaxValidator instance
        """
        return LogQLSyntaxValidator()
