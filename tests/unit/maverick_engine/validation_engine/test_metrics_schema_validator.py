"""
Unit tests for SchemaValidator.

Tests cover:
- Happy path with multiple valid metrics
- Failure when one or more metrics are missing
- Parser exception propagation
- Empty expression handling
- Bulk optimization for large metric sets
- Namespace isolation
"""

from unittest.mock import Mock, MagicMock, call

import pytest
import fakeredis

from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.validation_engine.metrics.metrics_schema_validator import MetricsSchemaValidator
from maverick_engine.validation_engine.metrics.structured_outputs import SchemaValidationResult
from maverick_engine.validation_engine.metrics.metric_expression_parser import MetricExpressionParseError


class MockMetricNameParser:
    """Mock parser implementation for testing."""

    def __init__(self, return_value: set[str] = None, raise_error: Exception = None):
        self._return_value = return_value or set()
        self._raise_error = raise_error
        self.parse_called = False
        self.last_expression = None

    def parse(self, metric_expression: str) -> set[str]:
        self.parse_called = True
        self.last_expression = metric_expression
        if self._raise_error:
            raise self._raise_error
        return self._return_value


@pytest.fixture
def redis_client():
    """Provide a fake Redis client for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def metadata_store(redis_client):
    """Provide a MetricsMetadataStore instance with fake Redis."""
    return MetricsMetadataStore(redis_client)


class TestMetricsSchemaValidator:
    """Test suite for MetricsSchemaValidator."""

    def test_all_metrics_valid(self, metadata_store):
        """Test validation succeeds when all metrics exist in namespace."""
        namespace = "test_ns"
        metrics = {"cpu.usage", "memory.total", "disk.io"}
        metadata_store.set_metric_names(namespace, metrics)

        parser = MockMetricNameParser(return_value=metrics)
        validator = MetricsSchemaValidator(metadata_store, parser)

        result = validator.validate(namespace, "cpu.usage + memory.total + disk.io")

        assert result.is_valid is True
        assert result.invalid_metrics == []
        assert result.error is None
        assert parser.parse_called is True

    def test_metricname_missing_in_metadata_store(self, metadata_store):
        """Test validation fails when one metric is missing."""
        namespace = "test_ns"
        valid_metrics = {"cpu.usage", "memory.total"}
        metadata_store.set_metric_names(namespace, valid_metrics)

        parser = MockMetricNameParser(return_value={"cpu.usage", "memory.total", "disk.io"})
        validator = MetricsSchemaValidator(metadata_store, parser)

        result = validator.validate(namespace, "cpu.usage + disk.io")

        assert result.is_valid is False
        assert "disk.io" in result.invalid_metrics
        assert len(result.invalid_metrics) == 1

    def test_parser_exception_propagation(self, metadata_store):
        """Test that parser exceptions are caught and returned as parse errors."""
        namespace = "test_ns"
        metadata_store.set_metric_names(namespace, {"cpu.usage", "cpu.usage.max"})

        parser = MockMetricNameParser(raise_error=MetricExpressionParseError("Error in parsing"))
        validator = MetricsSchemaValidator(metadata_store, parser)

        result = validator.validate(namespace, "cpu.usage / cpu.usage.max")

        assert result.is_valid is False
        assert result.invalid_metrics == []
        assert "Error in parsing" in result.error

    def test_empty_expression_success(self, metadata_store):
        """Test that empty expression returns success."""
        mock_store = Mock()
        parser = MockMetricNameParser()
        validator = MetricsSchemaValidator(mock_store, parser)

        result = validator.validate("ns", "")

        assert result.is_valid is True
        assert parser.parse_called is False
        mock_store.is_valid_metric_name.assert_not_called()

    def test_whitespace_expression_success(self, metadata_store):
        """Test that whitespace-only expression returns success."""
        mock_store = Mock()
        parser = MockMetricNameParser()
        validator = MetricsSchemaValidator(mock_store, parser)

        result = validator.validate("ns", "   \t\n  ")

        assert result.is_valid is True
        assert parser.parse_called is False

    def test_none_expression_success(self, metadata_store):
        """Test that None expression returns success."""
        mock_store = Mock()
        parser = MockMetricNameParser()
        validator = MetricsSchemaValidator(mock_store, parser)

        result = validator.validate("ns", None)

        assert result.is_valid is True

    def test_none_or_empty_namespace_error(self, metadata_store):
        """Test that None namespace returns error."""
        parser = MockMetricNameParser(return_value={"metric1"})
        validator = MetricsSchemaValidator(metadata_store, parser)

        result = validator.validate(None, "metric1")

        assert result.is_valid is False
        assert "Namespace cannot be blank" in result.error

        result = validator.validate("", "metric1")

        assert result.is_valid is False
        assert "Namespace cannot be blank" in result.error

    def test_empty_parser_result_failure(self, metadata_store):
        """Test that parser returning empty set returns failure."""
        mock_store = Mock()
        parser = MockMetricNameParser(return_value=set())
        validator = MetricsSchemaValidator(mock_store, parser)

        result = validator.validate("ns", "some expression with no metrics")

        assert result.is_valid is False
        mock_store.is_valid_metric_name.assert_not_called()

    def test_namespace_isolation(self, metadata_store):
        """Test that validation is isolated per namespace."""
        ns1 = "namespace1"
        ns2 = "namespace2"
        metadata_store.set_metric_names(ns1, {"metric_a", "metric_b"})
        metadata_store.set_metric_names(ns2, {"metric_x", "metric_y"})

        parser = MockMetricNameParser(return_value={"metric_a"})
        validator = MetricsSchemaValidator(metadata_store, parser)

        # metric_a exists in ns1
        result1 = validator.validate(ns1, "avg(metric_a)")
        assert result1.is_valid is True

        # metric_a does NOT exist in ns2
        result2 = validator.validate(ns2, "avg(metric_a)")
        assert result2.is_valid is False
        assert "metric_a" in result2.invalid_metrics

