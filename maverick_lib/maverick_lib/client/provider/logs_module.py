"""Common dependency injection module for logs operations (Spring-like pattern)."""

from maverick_engine.validation_engine.logs.log_query_validator import LogQueryValidator
from maverick_engine.validation_engine.logs.syntax import (
    LogQLSyntaxValidator,
    SplunkSPLSyntaxValidator,
)


class LogsModule:
    """Common module for logs operations - provides shared validator dependencies."""

    # Singleton instance of the log query validator
    _log_query_validator: LogQueryValidator | None = None

    @classmethod
    def get_log_query_validator(cls) -> LogQueryValidator:
        """
        Provide a LogQueryValidator instance with syntax validators.

        This method implements a singleton pattern - the validator is created only once
        and reused across all log clients.

        Returns:
            LogQueryValidator instance with LogQL and Splunk validators
        """
        if cls._log_query_validator is None:
            syntax_validators = {
                "loki": cls._get_logql_syntax_validator(),
                "splunk": cls._get_splunk_syntax_validator(),
            }
            cls._log_query_validator = LogQueryValidator(
                syntax_validators=syntax_validators
            )

        return cls._log_query_validator

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
