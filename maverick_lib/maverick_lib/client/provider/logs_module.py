"""Common dependency injection module for logs operations (Spring-like pattern)."""

from maverick_engine.validation_engine.logs.log_query_validator import LogQueryValidator
from maverick_engine.validation_engine.logs.syntax import (
    LogQLSyntaxValidator,
    SplunkSPLSyntaxValidator,
)
from opus_agent_base.config.config_manager import ConfigManager


class LogsModule:
    """Common module for logs operations - provides shared validator dependencies."""

    @classmethod
    def get_log_query_validator(cls, config_manager: ConfigManager) -> LogQueryValidator:
        """
        Provide a LogQueryValidator instance with syntax validators.

        Args:
            config_manager: ConfigManager instance for reading validation configuration

        Returns:
            LogQueryValidator instance with LogQL and Splunk validators
        """
        syntax_validators = {
            "loki": cls._get_logql_syntax_validator(),
            "splunk": cls._get_splunk_syntax_validator(),
        }
        return LogQueryValidator(
            syntax_validators=syntax_validators,
            config_manager=config_manager,
        )

    @classmethod
    def _get_logql_syntax_validator(cls) -> LogQLSyntaxValidator:
        """
        Provide a LogQLSyntaxValidator instance.

        Returns:
            LogQLSyntaxValidator instance
        """
        return LogQLSyntaxValidator()

    @classmethod
    def _get_splunk_syntax_validator(cls) -> SplunkSPLSyntaxValidator:
        """
        Provide a SplunkSPLSyntaxValidator instance.

        Returns:
            SplunkSPLSyntaxValidator instance
        """
        return SplunkSPLSyntaxValidator()
