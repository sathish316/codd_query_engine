"""Three-stage validator for Loki LogQL and Splunk SPL queries."""

from __future__ import annotations

import logging
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
from opus_agent_base.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class LogQueryValidator:
    """Executes syntax, schema, and semantic validation for log queries."""

    def __init__(
        self,
        syntax_validators: Mapping[str, LogsSyntaxValidator] | None = None,
        config_manager: ConfigManager | None = None,
    ):
        self.syntax_validators = syntax_validators or {
            "loki": LogQLSyntaxValidator(),
            "splunk": SplunkSPLSyntaxValidator(),
        }
        self._config_manager = config_manager

    def validate(
        self,
        backend: str,
        query: str,
        description: str,
        patterns: list[LogPattern],
    ) -> LogQueryValidationResult:
        # Determine config path based on backend
        if backend == "loki":
            syntax_enabled = self._config_manager.get_setting("mcp_config.logs.logql.validation.syntax.enabled", True)
        elif backend == "splunk":
            syntax_enabled = self._config_manager.get_setting("mcp_config.logs.splunk.validation.syntax.enabled", True)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

        # Stage 1: Syntax validation
        syntax_result = None
        if syntax_enabled:
            syntax_validator = self.syntax_validators.get(backend)
            if syntax_validator is None:
                raise ValueError(f"No syntax validator configured for backend: {backend}")

            syntax_result = syntax_validator.validate(query)
        else:
            logger.info(f"Syntax validation skipped for {backend} (disabled in config)")
            # Create a passing syntax result
            from maverick_engine.validation_engine.logs.structured_outputs import SyntaxValidationResult
            syntax_result = SyntaxValidationResult(is_valid=True, error=None)

        # TODO: Stage 2: Schema validation (when implemented)
        # TODO: Stage 3: Semantics validation (when implemented)

        return LogQueryValidationResult(
            syntax=syntax_result,
        )
