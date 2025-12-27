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
    """

    invalid_metrics: list[str] = Field(default_factory=list)

    @classmethod
    def success(cls) -> "SchemaValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, invalid_metrics=[])

    @classmethod
    def failure(
        cls, invalid_metrics: list[str], namespace: str
    ) -> "SchemaValidationResult":
        """Create a failure result with invalid metrics."""
        error_msg = cls._build_error_message(invalid_metrics, namespace)
        return cls(is_valid=False, invalid_metrics=invalid_metrics, error=error_msg)

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
        invalid_metrics: list[str], namespace: str, max_display: int = 5
    ) -> str:
        """Build a formatted error message for invalid metrics."""
        count = len(invalid_metrics)
        if count == 0:
            return ""

        displayed = invalid_metrics[:max_display]
        metrics_str = ", ".join(f"'{m}'" for m in displayed)

        if count > max_display:
            return f"Found {count} invalid metrics in namespace '{namespace}': {metrics_str}, and {count - max_display} more"
        return (
            f"Found {count} invalid metric(s) in namespace '{namespace}': {metrics_str}"
        )
