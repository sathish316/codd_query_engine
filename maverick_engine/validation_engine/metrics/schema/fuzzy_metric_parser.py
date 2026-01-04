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
        suggestion_limit: Number of suggestions to return for "did you mean" (default: 5)
        min_similarity_score: Minimum similarity score (0-100) to consider a match (default: 60)
    """

    def __init__(
        self,
        metadata_store: MetricsMetadataStore,
        top_k: int = 10,
        suggestion_limit: int = 5,
        min_similarity_score: float = 60.0,
    ):
        self._metadata_store = metadata_store
        self._namespace: str = ""
        self._top_k = top_k
        self._suggestion_limit = suggestion_limit
        self._min_similarity_score = min_similarity_score
        self._metric_index: Optional[list[str]] = None
        self._current_namespace: Optional[str] = None

    def set_namespace(self, namespace: str) -> None:
        """
        Set the namespace for metric validation.

        Reloads the metric index if the namespace changes.

        Args:
            namespace: The namespace to use for fetching valid metrics
        """
        if self._namespace != namespace:
            self._namespace = namespace
            self._metric_index = None  # Force reload on next parse
            self._current_namespace = None

    def _ensure_index_loaded(self):
        """Load the metric index if not already loaded."""
        if self._metric_index is None:
            valid_metrics = self._metadata_store.get_metric_names(self._namespace)
            self._metric_index = list(valid_metrics) if valid_metrics else []
            logger.info(
                f"Loaded metric index for namespace: {self._namespace}",
                extra={"metric_count": len(self._metric_index)}
            )

    def parse(self, metric_expression: str) -> set[str]:
        """
        Parse a metric expression and extract metric names using fuzzy matching.

        Uses rapidfuzz to find the top K most similar metric names, then checks
        if at least one has a substring match.

        Args:
            metric_expression: The expression string to parse

        Returns:
            Set of unique metric names found in the expression

        Raises:
            MetricExpressionParseError: If parsing fails
        """
        # Guard: empty expression
        if not metric_expression or not metric_expression.strip():
            logger.debug("Empty expression, returning empty set")
            return set()

        # Ensure the metric index is loaded
        self._ensure_index_loaded()

        if not self._metric_index:
            logger.warning(f"No valid metrics found for namespace: {self._namespace}")
            return set()

        # Find metrics that appear as substrings first (fast path)
        found_metrics = set()
        for metric in self._metric_index:
            if metric in metric_expression:
                found_metrics.add(metric)

        if found_metrics:
            logger.info(
                f"Found {len(found_metrics)} metrics using substring matching",
                extra={"metric_count": len(found_metrics), "namespace": self._namespace}
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
                self._metric_index,
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
            extra={"metric_count": len(found_metrics), "namespace": self._namespace}
        )

        return found_metrics

    def get_suggestions(self, metric_expression: str) -> list[tuple[str, float]]:
        """
        Get "did you mean" suggestions for metrics that might match.

        Returns the top N suggestions based on fuzzy matching scores.

        Args:
            metric_expression: The expression string to find suggestions for

        Returns:
            List of tuples (metric_name, similarity_score) sorted by score descending
        """
        # Ensure the metric index is loaded
        self._ensure_index_loaded()

        if not self._metric_index:
            return []

        # Extract potential metric name tokens from the expression
        tokens = re.findall(r'[a-z][a-z0-9_.]+', metric_expression.lower())

        if not tokens:
            return []

        # Collect all fuzzy matches across all tokens
        all_suggestions = []
        seen_metrics = set()

        for token in tokens:
            matches = process.extract(
                token,
                self._metric_index,
                scorer=fuzz.ratio,
                limit=self._suggestion_limit,
                score_cutoff=self._min_similarity_score
            )

            for match_name, score, _ in matches:
                if match_name not in seen_metrics:
                    all_suggestions.append((match_name, score))
                    seen_metrics.add(match_name)

        # Sort by score descending and limit to suggestion_limit
        all_suggestions.sort(key=lambda x: x[1], reverse=True)
        return all_suggestions[:self._suggestion_limit]
