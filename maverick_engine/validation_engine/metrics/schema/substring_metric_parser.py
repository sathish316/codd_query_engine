"""
Substring-based metric expression parser.

This module provides a MetricExpressionParser implementation that uses simple
substring matching to extract metric names from PromQL expressions.
"""

import logging
import re

from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.validation_engine.metrics.schema.metric_expression_parser import (
    MetricExpressionParser,
)

logger = logging.getLogger(__name__)


# Regex pattern for valid metric name characters
VALID_METRIC_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_.]*$")


class SubstringMetricParser(MetricExpressionParser):
    """
    Substring-based metric name parser.

    Extracts metric names by checking if any valid metric names from Redis
    appear as substrings in the expression.

    Args:
        metadata_store: MetricsMetadataStore instance for fetching valid metric names
    """

    def __init__(self, metadata_store: MetricsMetadataStore):
        self._metadata_store = metadata_store
        self._metric_index_by_namespace: dict[str, set[str]] = {}

    def _get_metric_index(self, namespace: str) -> set[str]:
        """
        Get metric index for namespace, loading lazily if needed.

        Args:
            namespace: The namespace to get metrics for

        Returns:
            Set of metric names for the namespace
        """
        if namespace not in self._metric_index_by_namespace:
            valid_metrics = self._metadata_store.get_metric_names(namespace)
            self._metric_index_by_namespace[namespace] = valid_metrics if valid_metrics else set()
            logger.info(
                f"Loaded metric index for namespace: {namespace}",
                extra={"metric_count": len(self._metric_index_by_namespace[namespace])}
            )
        return self._metric_index_by_namespace[namespace]

    def parse(self, metric_expression: str, namespace: str = "") -> set[str]:
        """
        Parse a metric expression and extract metric names using substring matching.

        Fetches all valid metric names for the namespace and checks if each appears
        as a substring in the expression.

        Args:
            metric_expression: The expression string to parse
            namespace: The namespace to validate metrics against

        Returns:
            Set of unique metric names found in the expression

        Raises:
            MetricExpressionParseError: If parsing fails
        """
        # Guard: empty expression
        if not metric_expression or not metric_expression.strip():
            logger.debug("Empty expression, returning empty set")
            return set()

        # Guard: namespace required
        if not namespace:
            logger.warning("Namespace not provided for SubstringMetricParser")
            return set()

        # Get all valid metric names for the namespace
        valid_metrics = self._get_metric_index(namespace)

        if not valid_metrics:
            logger.warning(f"No valid metrics found for namespace: {namespace}")
            return set()

        # Find metrics that appear as substrings in the expression
        found_metrics = set()
        for metric in valid_metrics:
            if metric in metric_expression:
                found_metrics.add(metric)

        logger.info(
            f"Found {len(found_metrics)} metrics using substring matching",
            extra={"metric_count": len(found_metrics), "namespace": namespace}
        )

        return found_metrics
