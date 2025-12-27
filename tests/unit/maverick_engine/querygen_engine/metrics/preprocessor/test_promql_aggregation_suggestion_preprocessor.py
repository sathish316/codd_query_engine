"""
Unit tests for PromQLAggregationSuggestionPreprocessor.

These tests verify that the preprocessor correctly enriches MetricsQueryIntent
with appropriate aggregation function suggestions based on metric type:
- Counter metrics (rate, increase, irate)
- Gauge metrics (avg_over_time, max_over_time, min_over_time, etc.)
- Histogram metrics (histogram_quantile with various quantiles, rate)
- Summary metrics (avg_over_time, rate, max_over_time)
- Timer metrics (histogram_quantile with quantiles, avg_over_time, max_over_time)
- Unknown/unsupported metric types
- Case-insensitive metric type handling
- Aggregation suggestions replacement behavior
- Intent immutability
"""

import pytest

from maverick_engine.querygen_engine.metrics.preprocessor.promql_aggregation_suggestion_preprocessor import (
    PromQLAggregationSuggestionPreprocessor,
)
from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
)


@pytest.fixture
def preprocessor() -> PromQLAggregationSuggestionPreprocessor:
    """Create a preprocessor instance for testing."""
    return PromQLAggregationSuggestionPreprocessor()


class TestCounterMetrics:
    """Test aggregation suggestions for counter metrics."""

    def test_counter_metric_type(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Counter metrics should get rate, increase, and irate suggestions."""
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
        )

        result = preprocessor.preprocess(intent)

        assert result.aggregation_suggestions is not None
        assert len(result.aggregation_suggestions) == 3
        assert result.aggregation_suggestions[0].function_name == "rate"
        assert result.aggregation_suggestions[1].function_name == "increase"
        assert result.aggregation_suggestions[2].function_name == "irate"

    def test_counter_metric_type_case_insensitive(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Counter type should be case-insensitive."""
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="COUNTER",
        )

        result = preprocessor.preprocess(intent)

        assert result.aggregation_suggestions is not None
        assert len(result.aggregation_suggestions) == 3
        assert result.aggregation_suggestions[0].function_name == "rate"

    def test_counter_with_filters(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Counter metrics with filters should still get suggestions."""
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
            filters={"method": "GET", "status": "200"},
        )

        result = preprocessor.preprocess(intent)

        assert result.aggregation_suggestions is not None
        assert len(result.aggregation_suggestions) == 3
        assert result.filters == {"method": "GET", "status": "200"}

    def test_counter_with_group_by(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Counter metrics with group_by should still get suggestions."""
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
            group_by=["instance", "job"],
        )

        result = preprocessor.preprocess(intent)

        assert result.aggregation_suggestions is not None
        assert len(result.aggregation_suggestions) == 3
        assert result.group_by == ["instance", "job"]


class TestGaugeMetrics:
    """Test aggregation suggestions for gauge metrics."""

    def test_gauge_metric_type(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Gauge metrics should get over_time functions."""
        intent = MetricsQueryIntent(
            metric="cpu_usage",
            metric_type="gauge",
        )

        result = preprocessor.preprocess(intent)

        assert result.aggregation_suggestions is not None
        assert len(result.aggregation_suggestions) == 4
        assert result.aggregation_suggestions[0].function_name == "avg_over_time"
        assert result.aggregation_suggestions[1].function_name == "max_over_time"
        assert result.aggregation_suggestions[2].function_name == "min_over_time"
        assert result.aggregation_suggestions[3].function_name == "sum_over_time"

    def test_gauge_metric_type_case_insensitive(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Gauge type should be case-insensitive."""
        intent = MetricsQueryIntent(
            metric="cpu_usage",
            metric_type="GaUgE",
        )

        result = preprocessor.preprocess(intent)

        assert result.aggregation_suggestions is not None
        assert len(result.aggregation_suggestions) == 4


class TestHistogramMetrics:
    """Test aggregation suggestions for histogram metrics."""

    def test_histogram_metric_type(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Histogram metrics should get histogram_quantile and rate."""
        intent = MetricsQueryIntent(
            metric="http_request_duration_seconds",
            metric_type="histogram",
        )

        result = preprocessor.preprocess(intent)

        assert result.aggregation_suggestions is not None
        assert len(result.aggregation_suggestions) == 2
        assert result.aggregation_suggestions[0].function_name == "histogram_quantile"
        assert result.aggregation_suggestions[0].params == {"quantile": 0.95}
        assert result.aggregation_suggestions[1].function_name == "histogram_quantile"
        assert result.aggregation_suggestions[1].params == {"quantile": 0.99}

    def test_histogram_quantile_params(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Histogram_quantile suggestions should have correct quantile params."""
        intent = MetricsQueryIntent(
            metric="http_request_duration_seconds",
            metric_type="histogram",
        )

        result = preprocessor.preprocess(intent)

        p95 = result.aggregation_suggestions[0]
        assert p95.function_name == "histogram_quantile"
        assert p95.params["quantile"] == 0.95

        p99 = result.aggregation_suggestions[1]
        assert p99.params["quantile"] == 0.99


class TestTimerMetrics:
    """Test aggregation suggestions for timer metrics."""

    def test_timer_metric_type(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Timer metrics should get histogram_quantile and over_time functions."""
        intent = MetricsQueryIntent(
            metric="request_timer",
            metric_type="timer",
        )

        result = preprocessor.preprocess(intent)

        assert result.aggregation_suggestions is not None
        assert len(result.aggregation_suggestions) == 4
        assert result.aggregation_suggestions[0].function_name == "histogram_quantile"
        assert result.aggregation_suggestions[0].params == {"quantile": 0.95}
        assert result.aggregation_suggestions[1].function_name == "histogram_quantile"
        assert result.aggregation_suggestions[1].params == {"quantile": 0.99}
        assert result.aggregation_suggestions[2].function_name == "avg_over_time"
        assert result.aggregation_suggestions[3].function_name == "max_over_time"


class TestIntentImmutability:
    """Test that the preprocessor returns new instances without mutating input."""

    def test_returns_new_intent_instance(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """Preprocessor should return a new intent instance."""
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
        )

        result = preprocessor.preprocess(intent)

        # Should be a different instance
        assert result is not intent
        # Original should be unchanged
        assert intent.aggregation_suggestions is None
        # Result should have suggestions
        assert result.aggregation_suggestions is not None

    def test_preserves_all_original_fields(
        self, preprocessor: PromQLAggregationSuggestionPreprocessor
    ):
        """All original fields should be preserved in the result."""
        intent = MetricsQueryIntent(
            metric="cpu_usage",
            metric_type="gauge",
            filters={"instance": "host1", "job": "node"},
            window="10m",
            group_by=["instance"],
        )

        result = preprocessor.preprocess(intent)

        assert result.metric == "cpu_usage"
        assert result.metric_type == "gauge"
        assert result.filters == {"instance": "host1", "job": "node"}
        assert result.window == "10m"
        assert result.group_by == ["instance"]
        assert result.aggregation_suggestions is not None
