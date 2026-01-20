"""
Unit tests for PromQLQuerygenPreprocessor.

These tests verify the conditional application of micrometer transformations
based on the QueryOpts.spring_micrometer_transform flag.
"""

import pytest
from unittest.mock import patch

from codd_engine.querygen_engine.metrics.preprocessor.promql_querygen_preprocessor import (
    PromQLQuerygenPreprocessor,
)
from codd_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent, QueryOpts


@pytest.fixture
def preprocessor() -> PromQLQuerygenPreprocessor:
    return PromQLQuerygenPreprocessor()


class TestMicrometerTransformConditional:
    """Tests for conditional micrometer transformation based on QueryOpts."""

    def test_micrometer_transform_applied_when_query_opts_flag_is_true(self, preprocessor):
        """Micrometer transformation should be applied when QueryOpts.spring_micrometer_transform is True."""
        intent = MetricsQueryIntent(
            metric="http_request_duration",
            meter_type="timer",
        )
        query_opts = QueryOpts(spring_micrometer_transform=True)

        # Mock the micrometer preprocessor to verify it's called
        with patch.object(
            preprocessor.micrometer_metricname_preprocessor,
            "preprocess",
            wraps=preprocessor.micrometer_metricname_preprocessor.preprocess,
        ) as mock_micrometer:
            result = preprocessor.preprocess(intent, query_opts)

            # Verify the micrometer preprocessor was called
            mock_micrometer.assert_called_once()

            # Verify the metric name was transformed (timer gets '_seconds' suffix)
            assert result.metric == "http_request_duration_seconds"

    def test_micrometer_transform_not_applied_when_query_opts_flag_is_false(self, preprocessor):
        """Micrometer transformation should not be applied when QueryOpts.spring_micrometer_transform is False."""
        intent = MetricsQueryIntent(
            metric="http_request_duration",
            meter_type="timer",
        )
        query_opts = QueryOpts(spring_micrometer_transform=False)

        # Mock the micrometer preprocessor to verify it's NOT called
        with patch.object(
            preprocessor.micrometer_metricname_preprocessor,
            "preprocess",
            wraps=preprocessor.micrometer_metricname_preprocessor.preprocess,
        ) as mock_micrometer:
            result = preprocessor.preprocess(intent, query_opts)

            # Verify the micrometer preprocessor was NOT called
            mock_micrometer.assert_not_called()

            # Verify the metric name was NOT transformed
            assert result.metric == "http_request_duration"

    def test_micrometer_transform_not_applied_when_query_opts_is_none(self, preprocessor):
        """Micrometer transformation should not be applied when query_opts is None."""
        intent = MetricsQueryIntent(
            metric="http_request_duration",
            meter_type="timer",
        )

        # Mock the micrometer preprocessor to verify it's NOT called
        with patch.object(
            preprocessor.micrometer_metricname_preprocessor,
            "preprocess",
            wraps=preprocessor.micrometer_metricname_preprocessor.preprocess,
        ) as mock_micrometer:
            result = preprocessor.preprocess(intent, None)

            # Verify the micrometer preprocessor was NOT called
            mock_micrometer.assert_not_called()

            # Verify the metric name was NOT transformed
            assert result.metric == "http_request_duration"

    def test_micrometer_transform_not_applied_with_default_query_opts(self, preprocessor):
        """Micrometer transformation should not be applied with default QueryOpts (spring_micrometer_transform=False)."""
        intent = MetricsQueryIntent(
            metric="http_request_duration",
            meter_type="timer",
        )
        query_opts = QueryOpts()  # Default: spring_micrometer_transform=False

        # Mock the micrometer preprocessor to verify it's NOT called
        with patch.object(
            preprocessor.micrometer_metricname_preprocessor,
            "preprocess",
            wraps=preprocessor.micrometer_metricname_preprocessor.preprocess,
        ) as mock_micrometer:
            result = preprocessor.preprocess(intent, query_opts)

            # Verify the micrometer preprocessor was NOT called
            mock_micrometer.assert_not_called()

            # Verify the metric name was NOT transformed
            assert result.metric == "http_request_duration"

    def test_aggregation_suggestions_always_applied(self, preprocessor):
        """Aggregation suggestions should always be applied regardless of QueryOpts."""
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            meter_type="counter",
        )
        query_opts = QueryOpts(spring_micrometer_transform=False)

        # Mock the aggregation preprocessor to verify it's called
        with patch.object(
            preprocessor.aggregation_suggestion_preprocessor,
            "preprocess",
            wraps=preprocessor.aggregation_suggestion_preprocessor.preprocess,
        ) as mock_aggregation:
            result = preprocessor.preprocess(intent, query_opts)

            # Verify the aggregation preprocessor was called
            mock_aggregation.assert_called_once()

            # Verify aggregation suggestions were added
            assert result.aggregation_suggestions is not None
            assert len(result.aggregation_suggestions) > 0
