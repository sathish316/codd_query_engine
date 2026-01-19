"""
Unit tests for PromQLQuerygenPreprocessor.

These tests verify the conditional application of micrometer transformations
based on the spring_micrometer_transform flag.
"""

import pytest
from unittest.mock import MagicMock, patch

from maverick_engine.querygen_engine.metrics.preprocessor.promql_querygen_preprocessor import (
    PromQLQuerygenPreprocessor,
)
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent


@pytest.fixture
def preprocessor() -> PromQLQuerygenPreprocessor:
    return PromQLQuerygenPreprocessor()


class TestMicrometerTransformConditional:
    """Tests for conditional micrometer transformation based on flag."""

    def test_micrometer_transform_applied_when_flag_is_true(self, preprocessor):
        """Micrometer transformation should be applied when spring_micrometer_transform is True."""
        # Create intent with spring_micrometer_transform=True
        intent = MetricsQueryIntent(
            metric="http_request_duration",
            metric_type="timer",
            spring_micrometer_transform=True,
        )

        # Mock the micrometer preprocessor to verify it's called
        with patch.object(
            preprocessor.micrometer_metricname_preprocessor,
            "preprocess",
            wraps=preprocessor.micrometer_metricname_preprocessor.preprocess,
        ) as mock_micrometer:
            result = preprocessor.preprocess(intent)

            # Verify the micrometer preprocessor was called
            mock_micrometer.assert_called_once()

            # Verify the metric name was transformed (timer gets '_seconds' suffix)
            assert result.metric == "http_request_duration_seconds"

    def test_micrometer_transform_not_applied_when_flag_is_false(self, preprocessor):
        """Micrometer transformation should not be applied when spring_micrometer_transform is False."""
        # Create intent with spring_micrometer_transform=False (default)
        intent = MetricsQueryIntent(
            metric="http_request_duration",
            metric_type="timer",
            spring_micrometer_transform=False,
        )

        # Mock the micrometer preprocessor to verify it's NOT called
        with patch.object(
            preprocessor.micrometer_metricname_preprocessor,
            "preprocess",
            wraps=preprocessor.micrometer_metricname_preprocessor.preprocess,
        ) as mock_micrometer:
            result = preprocessor.preprocess(intent)

            # Verify the micrometer preprocessor was NOT called
            mock_micrometer.assert_not_called()

            # Verify the metric name was NOT transformed
            assert result.metric == "http_request_duration"

    def test_aggregation_suggestions_always_applied(self, preprocessor):
        """Aggregation suggestions should always be applied regardless of micrometer flag."""
        # Create intent with spring_micrometer_transform=False
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
            spring_micrometer_transform=False,
        )

        # Mock the aggregation preprocessor to verify it's called
        with patch.object(
            preprocessor.aggregation_suggestion_preprocessor,
            "preprocess",
            wraps=preprocessor.aggregation_suggestion_preprocessor.preprocess,
        ) as mock_aggregation:
            result = preprocessor.preprocess(intent)

            # Verify the aggregation preprocessor was called
            mock_aggregation.assert_called_once()

            # Verify aggregation suggestions were added
            assert result.aggregation_suggestions is not None
            assert len(result.aggregation_suggestions) > 0

    def test_both_preprocessors_applied_when_flag_is_true(self, preprocessor):
        """Both aggregation and micrometer preprocessors should be applied when flag is True."""
        intent = MetricsQueryIntent(
            metric="http_request_duration",
            metric_type="timer",
            spring_micrometer_transform=True,
        )

        result = preprocessor.preprocess(intent)

        # Verify both transformations were applied
        assert result.metric == "http_request_duration_seconds"  # micrometer transform
        assert result.aggregation_suggestions is not None  # aggregation suggestions
        assert len(result.aggregation_suggestions) > 0
