from __future__ import annotations

from typing import Protocol

from codd_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from codd_engine.validation_engine.metrics.semantics.structured_outputs import (
    SemanticValidationResult,
)


class MetricsSemanticsValidator(Protocol):
    """Protocol for validating metrics query semantics (e.g., PromQL, OpenTSDB, SignalFX etc)."""

    def validate(
        self, original_intent: MetricsQueryIntent, generated_query: str
    ) -> SemanticValidationResult:
        """
        Validate the semantics of a metrics query against the original intent.

        Args:
            original_intent: The original metrics query intent
            generated_query: The generated query string to validate

        Returns:
            SemanticValidationResult indicating whether query matches intent
        """
        ...
