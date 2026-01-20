"""Protocol for metrics syntax validators."""

from __future__ import annotations

from typing import Protocol

from codd_engine.validation_engine.grammar_validator import SyntaxValidationResult


class MetricsSyntaxValidator(Protocol):
    """Protocol for validating metrics query syntax (e.g., PromQL, OpenTSDB, SignalFX etc)."""

    def validate(self, query: str) -> SyntaxValidationResult:
        """Validate the syntax of a metrics query."""
        ...
