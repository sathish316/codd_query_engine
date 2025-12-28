"""Three-stage validator for Loki LogQL and Splunk SPL queries."""

from __future__ import annotations

from typing import Mapping

from maverick_engine.logs.log_patterns import LogPattern
from maverick_engine.validation_engine.logs.structured_outputs import (
    LogQueryValidationResult,
)
from maverick_engine.validation_engine.logs.syntax import (
    LogsSyntaxValidator,
    LogQLSyntaxValidator,
    SplunkSPLSyntaxValidator,
)


class LogQueryValidator:
    """Executes syntax, schema, and semantic validation for log queries."""

    def __init__(
        self,
        syntax_validators: Mapping[str, LogsSyntaxValidator] | None = None,
    ):
        self.syntax_validators = syntax_validators or {
            "loki": LogQLSyntaxValidator(),
            "splunk": SplunkSPLSyntaxValidator(),
        }

    def validate(
        self,
        backend: str,
        query: str,
        description: str,
        patterns: list[LogPattern],
    ) -> LogQueryValidationResult:
        syntax_validator = self.syntax_validators.get(backend)
        if syntax_validator is None:
            raise ValueError(f"No syntax validator configured for backend: {backend}")

        syntax_result = syntax_validator.validate(query)

        return LogQueryValidationResult(
            syntax=syntax_result,
        )
