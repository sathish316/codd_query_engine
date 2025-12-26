from dataclasses import replace
from typing import Mapping, Sequence

from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.querygen_engine.metrics.preprocessor.metrics_querygen_preprocessor import MetricsQuerygenPreprocessor


class PromQLQuerygenPreprocessor(MetricsQuerygenPreprocessor):
    """
    Preprocessor for PromQL MetricsQueryIntent.
    """

    def __init__(self):
        """
        Initialize the preprocessor.
        """
        self.suggested_aggregation_preprocessor = PromQLSuggestedAggregationPreprocessor()
        self.actuator_metrics_preprocessor = PromQLActuatorMetricsPreprocessor()

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
        intent = self.suggested_aggregation_preprocessor.preprocess(intent)
        intent = self.actuator_metrics_preprocessor.preprocess(intent)
        return intent
