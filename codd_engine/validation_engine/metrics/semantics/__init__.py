"""Semantic validation for metrics queries."""

from codd_engine.validation_engine.metrics.semantics.structured_outputs import (
    SemanticValidationResult,
)

# Note: PromQLSemanticsValidator is not imported here to avoid circular imports.
# Import directly from codd_engine.validation_engine.metrics.semantics.promql_semantics_validator

__all__ = [
    "SemanticValidationResult",
]
