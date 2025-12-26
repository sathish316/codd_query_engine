import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
# TODO: use BaseModel
class SchemaValidationResult:
    """
    Result of schema validation for a metric expression.

    Attributes:
        is_valid: True if all metrics exist in namespace, False otherwise
        invalid_metrics: List of metric names not found in namespace
        error: Optional error message for parser failures or other issues
    """
    is_valid: bool
    invalid_metrics: list[str] = field(default_factory=list)
    error: Optional[str] = None

    @classmethod
    def success(cls) -> "SchemaValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, invalid_metrics=[])

    @classmethod
    def failure(cls, invalid_metrics: list[str], namespace: str) -> "SchemaValidationResult":
        """Create a failure result with invalid metrics."""
        error_msg = cls._build_error_message(invalid_metrics, namespace)
        return cls(is_valid=False, invalid_metrics=invalid_metrics, error=error_msg)

    @classmethod
    def parse_error(cls, message: str, original_exception: Optional[Exception] = None) -> "SchemaValidationResult":
        """Create a result for parser failures."""
        error_msg = f"Expression parse error: {message}"
        if original_exception:
            logger.warning(
                "Parser exception during schema validation",
                exc_info=original_exception
            )
        return cls(is_valid=False, invalid_metrics=[], error=error_msg)

    @staticmethod
    def _build_error_message(invalid_metrics: list[str], namespace: str, max_display: int = 5) -> str:
        """Build a formatted error message for invalid metrics."""
        count = len(invalid_metrics)
        if count == 0:
            return ""

        displayed = invalid_metrics[:max_display]
        metrics_str = ", ".join(f"'{m}'" for m in displayed)

        if count > max_display:
            return f"Found {count} invalid metrics in namespace '{namespace}': {metrics_str}, and {count - max_display} more"
        return f"Found {count} invalid metric(s) in namespace '{namespace}': {metrics_str}"

