from __future__ import annotations

from typing import Protocol

from maverick_engine.validation_engine.metrics.semantics.structured_outputs import SemanticValidationResult
from maverick_engine.validation_engine.metrics.validator import Validator

class MetricsSemanticsValidator(Protocol):
    """Protocol for validating metrics query semantics (e.g., PromQL, OpenTSDB, SignalFX etc)."""

    def validate(self, query: str) -> SemanticValidationResult:
        """
        Validate the semantics of a metrics query.
        """
        ...
