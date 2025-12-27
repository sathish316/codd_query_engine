from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.querygen_engine.metrics.preprocessor.metrics_querygen_preprocessor import (
    MetricsQuerygenPreprocessor,
)
from maverick_engine.querygen_engine.metrics.preprocessor.promql_aggregation_suggestion_preprocessor import (
    PromQLAggregationSuggestionPreprocessor,
)
from maverick_engine.querygen_engine.metrics.preprocessor.promql_micrometer_metricname_preprocessor import (
    PromQLMicrometerMetricNamePreprocessor,
)


class PromQLQuerygenPreprocessor(MetricsQuerygenPreprocessor):
    """
    Preprocessor for PromQL MetricsQueryIntent.
    """

    def __init__(self):
        """
        Initialize the preprocessor.
        """
        self.aggregation_suggestion_preprocessor = (
            PromQLAggregationSuggestionPreprocessor()
        )
        self.micrometer_metricname_preprocessor = (
            PromQLMicrometerMetricNamePreprocessor()
        )

    def preprocess(self, intent: MetricsQueryIntent) -> MetricsQueryIntent:
        """
        Apply preprocessing steps before query generation:
        1. Ensure the intent contains suggested aggregations for the metric type.
        2. Ensure the intent transforms SpringBoot metric names to valid Prometheus metric names

        Args:
            intent: The query intent to preprocess

        Returns:
            Preprocessed Query intent
        """
        intent = self.aggregation_suggestion_preprocessor.preprocess(intent)
        # intent = self.micrometer_metricname_preprocessor.preprocess(intent)
        return intent
