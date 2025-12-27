from typing import Mapping, Sequence
from maverick_engine.querygen_engine.metrics.structured_inputs import (
    AggregationFunctionSuggestion,
)
from maverick_engine.querygen_engine.metrics.preprocessor.metrics_querygen_preprocessor import (
    MetricsQuerygenPreprocessor,
)
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent

DEFAULT_AGGREGATION_SUGGESTIONS: Mapping[
    str, Sequence[AggregationFunctionSuggestion]
] = {
    "counter": [
        AggregationFunctionSuggestion(function_name="rate"),
        AggregationFunctionSuggestion(function_name="increase"),
        AggregationFunctionSuggestion(function_name="irate"),
    ],
    "gauge": [
        AggregationFunctionSuggestion(function_name="avg_over_time"),
        AggregationFunctionSuggestion(function_name="max_over_time"),
        AggregationFunctionSuggestion(function_name="min_over_time"),
        AggregationFunctionSuggestion(function_name="sum_over_time"),
    ],
    "histogram": [
        AggregationFunctionSuggestion(
            function_name="histogram_quantile", params={"quantile": 0.95}
        ),
        AggregationFunctionSuggestion(
            function_name="histogram_quantile", params={"quantile": 0.99}
        ),
    ],
    "timer": [
        AggregationFunctionSuggestion(
            function_name="histogram_quantile", params={"quantile": 0.95}
        ),
        AggregationFunctionSuggestion(
            function_name="histogram_quantile", params={"quantile": 0.99}
        ),
        AggregationFunctionSuggestion(function_name="avg_over_time"),
        AggregationFunctionSuggestion(function_name="max_over_time"),
    ],
}


class PromQLAggregationSuggestionPreprocessor(MetricsQuerygenPreprocessor):
    """
    Preprocessor for PromQL MetricsQueryIntent.
    """

    def __init__(self):
        """
        Initialize the preprocessor.
        """
        pass

    def preprocess(self, intent: MetricsQueryIntent) -> MetricsQueryIntent:
        """
        Enrich the intent with suggested aggregation functions.

        If the intent already has aggregation_suggestions, it is returned unchanged.
        Otherwise, selects the primary (first) suggestion based on the metric type.

        Args:
            intent: The query intent to preprocess

        Returns:
            Query intent with aggregation_suggestions populated
        """
        metric_type = (intent.metric_type or "").lower()
        aggregation_suggestions = DEFAULT_AGGREGATION_SUGGESTIONS.get(metric_type, [])

        if not aggregation_suggestions:
            return intent

        return intent.clone_with(aggregation_suggestions=aggregation_suggestions)
