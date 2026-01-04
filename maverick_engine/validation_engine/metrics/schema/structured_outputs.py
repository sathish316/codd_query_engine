import logging
from typing import Optional

from pydantic import Field

from maverick_engine.validation_engine.metrics.validation_result import ValidationResult

logger = logging.getLogger(__name__)


class SchemaValidationResult(ValidationResult):
    """
    Result of schema validation for a metric expression.

    Extends the base ValidationResult with schema-specific fields for tracking
    which metrics are invalid in the namespace.

    Attributes:
        is_valid: Inherited from ValidationResult - True if all metrics exist in namespace
        error: Inherited from ValidationResult - Error message for parser failures or other issues
        invalid_metrics: List of metric names not found in namespace
        suggestions: Optional "did you mean" suggestions as list of (metric_name, score) tuples
    """

    invalid_metrics: list[str] = Field(default_factory=list)
    suggestions: list[tuple[str, float]] = Field(default_factory=list)

    @classmethod
    def success(cls) -> "SchemaValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, invalid_metrics=[])

    @classmethod
    def failure(
        cls,
        invalid_metrics: list[str],
        namespace: str,
        suggestions: Optional[list[tuple[str, float]]] = None
    ) -> "SchemaValidationResult":
        """Create a failure result with invalid metrics and optional suggestions."""
        error_msg = cls._build_error_message(
            invalid_metrics, namespace, suggestions or []
        )
        return cls(
            is_valid=False,
            invalid_metrics=invalid_metrics,
            suggestions=suggestions or [],
            error=error_msg
        )

    @classmethod
    def parse_error(
        cls, message: str, original_exception: Optional[Exception] = None
    ) -> "SchemaValidationResult":
        """Create a result for parser failures."""
        error_msg = f"Expression parse error: {message}"
        if original_exception:
            logger.warning(
                "Parser exception during schema validation", exc_info=original_exception
            )
        return cls(is_valid=False, invalid_metrics=[], error=error_msg)

    @staticmethod
    def _build_error_message(
        invalid_metrics: list[str],
        namespace: str,
        suggestions: list[tuple[str, float]],
        max_display: int = 5
    ) -> str:
        """Build a formatted error message for invalid metrics with optional suggestions."""
        count = len(invalid_metrics)
        if count == 0:
            return ""

        displayed = invalid_metrics[:max_display]
        metrics_str = ", ".join(f"'{m}'" for m in displayed)

        base_msg = ""
        if count > max_display:
            base_msg = f"Found {count} invalid metrics in namespace '{namespace}': {metrics_str}, and {count - max_display} more"
        else:
            base_msg = f"Found {count} invalid metric(s) in namespace '{namespace}': {metrics_str}"

        # Add suggestions if available
        if suggestions:
            suggestions_str = ", ".join(
                f"'{name}' (score: {score:.0f})" for name, score in suggestions
            )
            base_msg += f". Did you mean: {suggestions_str}?"

        return base_msg
