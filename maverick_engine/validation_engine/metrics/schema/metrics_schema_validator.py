"""
Schema validator for metric expressions.

This module validates that all metric names referenced in a metric expression
exist within the caller's namespace.

Uses MetricsMetadataStore for namespace-aware checks.
"""

import logging

from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.validation_engine.metrics.schema.metric_expression_parser import (
    MetricExpressionParser,
    MetricExpressionParseError,
)
from maverick_engine.validation_engine.metrics.schema.structured_outputs import SchemaValidationResult

logger = logging.getLogger(__name__)


class MetricsSchemaValidator:
    """
    Validates that metric expressions reference only existing metrics.

    Args:
        metadata_store: MetricsMetadataStore instance
        parser: MetricExpressionParser for extracting metric names
    """

    def __init__(
        self,
        metadata_store: MetricsMetadataStore,
        parser: MetricExpressionParser,
    ):
        self._metadata_store = metadata_store
        self._parser = parser

    def validate(self, namespace: str, metric_expression: str) -> SchemaValidationResult:
        """
        Validate metric names in expression are valid.

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
        if not namespace or not namespace.strip():
            return SchemaValidationResult.parse_error("Namespace cannot be blank")

        # Parse expression to extract metric names
        try:
            metric_names = self._parser.parse(metric_expression)
        except MetricExpressionParseError as e:
            return SchemaValidationResult.parse_error(str(e), e)
        except Exception as e:
            return SchemaValidationResult.parse_error(f"Unexpected parser error: {e}", e)

        # Guard: no metrics found in expression
        if not metric_names:
            logger.warning("No metrics found in expression, validation failed")
            return SchemaValidationResult.parse_error("No metrics found in expression")

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
        return self._find_invalid_individual(namespace, metrics)

    def _find_invalid_individual(self, namespace: str, metrics: set[str]) -> list[str]:
        """Check each metric individually using is_valid_metric_name."""
        invalid = []
        for metric in metrics:
            if not self._metadata_store.is_valid_metric_name(namespace, metric):
                invalid.append(metric)
        return invalid
