"""
Fuzzy matching-based metric expression parser.

This module provides a MetricExpressionParser implementation that uses rapidfuzz
for fuzzy matching to extract metric names from PromQL expressions.
"""

import logging
import re
from typing import Optional

from rapidfuzz import fuzz, process

from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.validation_engine.metrics.schema.metric_expression_parser import (
    MetricExpressionParser,
)

logger = logging.getLogger(__name__)


# Regex pattern for valid metric name characters
VALID_METRIC_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_.]*$")


class FuzzyMetricParser(MetricExpressionParser):
    """
    Fuzzy matching-based metric name parser.

    Extracts metric names using rapidfuzz to find similar metric names
    from the valid metrics in Redis. Maintains an in-memory index per namespace.

    Args:
        metadata_store: MetricsMetadataStore instance for fetching valid metric names
        top_k: Number of fuzzy matches to consider (default: 10)
        min_similarity_score: Minimum similarity score (0-100) to consider a match (default: 60)
    """

    def __init__(
        self,
        metadata_store: MetricsMetadataStore,
        top_k: int = 10,
        min_similarity_score: float = 60.0,
    ):
        self._metadata_store = metadata_store
        self._top_k = top_k
        self._min_similarity_score = min_similarity_score
        self._metric_index_by_namespace: dict[str, list[str]] = {}

    def _get_metric_index(self, namespace: str) -> list[str]:
        """
        Get metric index for namespace, loading lazily if needed.

        Args:
            namespace: The namespace to get metrics for

        Returns:
            List of metric names for the namespace
        """
        if namespace not in self._metric_index_by_namespace:
            valid_metrics = self._metadata_store.get_metric_names(namespace)
            self._metric_index_by_namespace[namespace] = list(valid_metrics) if valid_metrics else []
            logger.info(
                f"Loaded metric index for namespace: {namespace}",
                extra={"metric_count": len(self._metric_index_by_namespace[namespace])}
            )
        return self._metric_index_by_namespace[namespace]

    def parse(self, metric_expression: str, namespace: str = "") -> set[str]:
        """
        Parse a metric expression and extract metric names using fuzzy matching.

        Uses rapidfuzz to find the top K most similar metric names, then checks
        if at least one has a substring match.

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
            logger.warning("Namespace not provided for FuzzyMetricParser")
            return set()

        # Get metric index for namespace
        metric_index = self._get_metric_index(namespace)

        if not metric_index:
            logger.warning(f"No valid metrics found for namespace: {namespace}")
            return set()

        # Find metrics that appear as substrings first (fast path)
        found_metrics = set()
        for metric in metric_index:
            if metric in metric_expression:
                found_metrics.add(metric)

        if found_metrics:
            logger.info(
                f"Found {len(found_metrics)} metrics using substring matching",
                extra={"metric_count": len(found_metrics), "namespace": namespace}
            )
            return found_metrics

        # If no exact substring matches, use fuzzy matching
        # Extract potential metric name tokens from the expression
        # Look for alphanumeric sequences that could be metric names
        tokens = re.findall(r'[a-z][a-z0-9_.]+', metric_expression.lower())

        if not tokens:
            logger.debug("No potential metric tokens found in expression")
            return set()

        # For each token, find fuzzy matches
        for token in tokens:
            matches = process.extract(
                token,
                metric_index,
                scorer=fuzz.ratio,
                limit=self._top_k,
                score_cutoff=self._min_similarity_score
            )

            # Check if any fuzzy match has a substring match in the original expression
            for match_name, score, _ in matches:
                if match_name in metric_expression:
                    found_metrics.add(match_name)
                    logger.debug(
                        f"Fuzzy match found: {match_name} (score: {score:.1f}) for token: {token}"
                    )

        logger.info(
            f"Found {len(found_metrics)} metrics using fuzzy matching",
            extra={"metric_count": len(found_metrics), "namespace": namespace}
        )

        return found_metrics
