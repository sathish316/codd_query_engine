"""
Protocol for metrics syntax validators.

This module defines the interface that all metrics syntax validators must implement.
"""

from __future__ import annotations

from typing import Protocol

from maverick_engine.validation_engine.metrics.syntax.structured_outputs import SyntaxValidationResult


class MetricsSyntaxValidator(Protocol):
    """Protocol for validating metrics query syntax (e.g., PromQL, OpenTSDB, SignalFX etc)."""

    def validate(self, query: str) -> SyntaxValidationResult:
        """
        Validate the syntax of a metrics query.

        Args:
            query: The query string to validate

        Returns:
            SyntaxValidationResult indicating whether the query is syntactically valid
        """
        ...

