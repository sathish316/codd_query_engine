"""
Schema validator for metric expressions.

This module validates that all metric names referenced in a metric expression
exist within the caller's namespace before the expression is executed.
Uses MetricsMetadataClient for namespace-aware membership checks.
"""

import logging
from dataclasses import dataclass, field
from typing import Protocol, Optional

logger = logging.getLogger(__name__)


class MetricExpressionParseError(Exception):
    """Raised when a metric expression cannot be parsed."""
    pass


class MetricExpressionParser(Protocol):
    """
    Protocol for parsing metric expressions to extract metric names.

    Implementations should be synchronous and raise MetricExpressionParseError
    or generic Exception on parse failures.
    """

    def parse(self, metric_expression: str) -> set[str]:
        """
        Parse a metric expression and extract unique metric names.

        Args:
            metric_expression: The expression string to parse

        Returns:
            Set of unique metric names found in the expression

        Raises:
            MetricExpressionParseError: If the expression is malformed
        """
        ...


@dataclass
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


class SchemaValidator:
    """
    Validates that metric expressions reference only existing metrics.

    Uses MetricsMetadataClient for namespace-aware membership checks and
    an injected parser to extract metric names from expressions.

    Args:
        metadata_client: MetricsMetadataClient instance for Redis operations
        parser: MetricExpressionParser implementation for extracting metric names
        bulk_fetch_threshold: Number of metrics above which bulk fetch is used (default: 5)
    """

    DEFAULT_BULK_FETCH_THRESHOLD = 5

    def __init__(
        self,
        metadata_client,  # MetricsMetadataClient - not type hinted to avoid import
        parser: MetricExpressionParser,
        bulk_fetch_threshold: int = DEFAULT_BULK_FETCH_THRESHOLD
    ):
        self._metadata_client = metadata_client
        self._parser = parser
        self._bulk_fetch_threshold = bulk_fetch_threshold

    def validate(self, namespace: str, metric_expression: str) -> SchemaValidationResult:
        """
        Validate that all metrics in the expression exist in the namespace.

        Args:
            namespace: The namespace to check metrics against
            metric_expression: The metric expression to validate

        Returns:
            SchemaValidationResult indicating success or failure with details
        """
        # Guard: empty expression is valid (no metrics to check)
        if not metric_expression or not metric_expression.strip():
            logger.debug("Empty expression, validation succeeded")
            return SchemaValidationResult.success()

        # Guard: empty namespace
        if namespace is None:
            return SchemaValidationResult.parse_error("Namespace cannot be None")

        # Parse expression to extract metric names
        try:
            metric_names = self._parser.parse(metric_expression)
        except MetricExpressionParseError as e:
            return SchemaValidationResult.parse_error(str(e), e)
        except Exception as e:
            return SchemaValidationResult.parse_error(f"Unexpected parser error: {e}", e)

        # Guard: no metrics found in expression
        if not metric_names:
            logger.debug("No metrics found in expression, validation succeeded")
            return SchemaValidationResult.success()

        # Deduplicate and validate
        unique_metrics = set(metric_names)
        invalid_metrics = self._find_invalid_metrics(namespace, unique_metrics)

        if invalid_metrics:
            logger.warning(
                "Schema validation failed",
                extra={
                    "namespace": namespace,
                    "invalid_count": len(invalid_metrics),
                    "total_metrics": len(unique_metrics)
                }
            )
            return SchemaValidationResult.failure(sorted(invalid_metrics), namespace)

        logger.info(
            "Schema validation succeeded",
            extra={
                "namespace": namespace,
                "metric_count": len(unique_metrics)
            }
        )
        return SchemaValidationResult.success()

    def _find_invalid_metrics(self, namespace: str, metrics: set[str]) -> list[str]:
        """
        Find metrics that do not exist in the namespace.

        Uses bulk fetch optimization when number of metrics exceeds threshold.

        Args:
            namespace: The namespace to check against
            metrics: Set of metric names to validate

        Returns:
            List of metric names not found in namespace
        """
        if len(metrics) >= self._bulk_fetch_threshold:
            return self._find_invalid_bulk(namespace, metrics)
        return self._find_invalid_individual(namespace, metrics)

    def _find_invalid_individual(self, namespace: str, metrics: set[str]) -> list[str]:
        """Check each metric individually using is_valid_metric_name."""
        invalid = []
        for metric in metrics:
            if not self._metadata_client.is_valid_metric_name(namespace, metric):
                invalid.append(metric)
        return invalid

    def _find_invalid_bulk(self, namespace: str, metrics: set[str]) -> list[str]:
        """Fetch all namespace metrics once and check membership locally."""
        valid_metrics = self._metadata_client.get_metric_names(namespace)
        return [m for m in metrics if m not in valid_metrics]
