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

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, call

# Add parent directory to path to allow imports from maverick-engine
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import fakeredis

# Import using relative path since directory has hyphen
import importlib.util

# Import MetricsMetadataClient
spec_client = importlib.util.spec_from_file_location(
    "metrics_metadata_client",
    project_root / "maverick-dal" / "metrics" / "metrics_metadata_client.py"
)
metrics_metadata_client = importlib.util.module_from_spec(spec_client)
spec_client.loader.exec_module(metrics_metadata_client)
MetricsMetadataClient = metrics_metadata_client.MetricsMetadataClient

# Import SchemaValidator and related types
spec_validator = importlib.util.spec_from_file_location(
    "schema_validator",
    project_root / "maverick-engine" / "validation_engine" / "schema_validator.py"
)
schema_validator = importlib.util.module_from_spec(spec_validator)
spec_validator.loader.exec_module(schema_validator)
SchemaValidator = schema_validator.SchemaValidator
SchemaValidationResult = schema_validator.SchemaValidationResult
MetricExpressionParseError = schema_validator.MetricExpressionParseError


class MockParser:
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
def metadata_client(redis_client):
    """Provide a MetricsMetadataClient instance with fake Redis."""
    return MetricsMetadataClient(redis_client)


class TestSchemaValidationResult:
    """Tests for SchemaValidationResult dataclass."""

    def test_success_result(self):
        """Test creating a success result."""
        result = SchemaValidationResult.success()
        assert result.is_valid is True
        assert result.invalid_metrics == []
        assert result.error is None

    def test_failure_result(self):
        """Test creating a failure result with invalid metrics."""
        invalid = ["metric1", "metric2"]
        result = SchemaValidationResult.failure(invalid, "test_namespace")
        assert result.is_valid is False
        assert result.invalid_metrics == invalid
        assert "metric1" in result.error
        assert "metric2" in result.error
        assert "test_namespace" in result.error

    def test_parse_error_result(self):
        """Test creating a parse error result."""
        result = SchemaValidationResult.parse_error("Invalid syntax")
        assert result.is_valid is False
        assert result.invalid_metrics == []
        assert "Expression parse error" in result.error
        assert "Invalid syntax" in result.error

    def test_error_message_truncation(self):
        """Test that error message truncates long metric lists."""
        invalid = [f"metric{i}" for i in range(10)]
        result = SchemaValidationResult.failure(invalid, "ns")
        # Should show first 5 and indicate more
        assert "10 invalid metrics" in result.error
        assert "and 5 more" in result.error


class TestSchemaValidator:
    """Test suite for SchemaValidator."""

    def test_init(self, metadata_client):
        """Test validator initialization."""
        parser = MockParser()
        validator = SchemaValidator(metadata_client, parser)
        assert validator._metadata_client is metadata_client
        assert validator._parser is parser
        assert validator._bulk_fetch_threshold == SchemaValidator.DEFAULT_BULK_FETCH_THRESHOLD

    def test_init_custom_threshold(self, metadata_client):
        """Test validator initialization with custom threshold."""
        parser = MockParser()
        validator = SchemaValidator(metadata_client, parser, bulk_fetch_threshold=10)
        assert validator._bulk_fetch_threshold == 10

    def test_happy_path_all_metrics_valid(self, metadata_client):
        """Test validation succeeds when all metrics exist in namespace."""
        namespace = "test_ns"
        metrics = {"cpu.usage", "memory.total", "disk.io"}
        metadata_client.set_metric_names(namespace, metrics)

        parser = MockParser(return_value=metrics)
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "cpu.usage + memory.total + disk.io")

        assert result.is_valid is True
        assert result.invalid_metrics == []
        assert result.error is None
        assert parser.parse_called is True

    def test_failure_one_metric_missing(self, metadata_client):
        """Test validation fails when one metric is missing."""
        namespace = "test_ns"
        valid_metrics = {"cpu.usage", "memory.total"}
        metadata_client.set_metric_names(namespace, valid_metrics)

        parser = MockParser(return_value={"cpu.usage", "memory.total", "disk.io"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "cpu.usage + disk.io")

        assert result.is_valid is False
        assert "disk.io" in result.invalid_metrics
        assert len(result.invalid_metrics) == 1

    def test_failure_multiple_metrics_missing(self, metadata_client):
        """Test validation fails with multiple missing metrics."""
        namespace = "test_ns"
        valid_metrics = {"cpu.usage"}
        metadata_client.set_metric_names(namespace, valid_metrics)

        parser = MockParser(return_value={"cpu.usage", "memory.total", "disk.io", "network.bytes"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "expr")

        assert result.is_valid is False
        assert len(result.invalid_metrics) == 3
        assert "memory.total" in result.invalid_metrics
        assert "disk.io" in result.invalid_metrics
        assert "network.bytes" in result.invalid_metrics

    def test_parser_exception_propagation(self, metadata_client):
        """Test that parser exceptions are caught and returned as parse errors."""
        namespace = "test_ns"
        metadata_client.set_metric_names(namespace, {"metric1"})

        parser = MockParser(raise_error=MetricExpressionParseError("Invalid syntax at position 5"))
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "invalid expression")

        assert result.is_valid is False
        assert result.invalid_metrics == []
        assert "Expression parse error" in result.error
        assert "Invalid syntax at position 5" in result.error

    def test_parser_generic_exception_propagation(self, metadata_client):
        """Test that generic parser exceptions are caught and handled."""
        namespace = "test_ns"

        parser = MockParser(raise_error=ValueError("Unexpected error"))
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "expression")

        assert result.is_valid is False
        assert "Unexpected parser error" in result.error

    def test_parser_exception_no_redis_call(self, metadata_client):
        """Test that parser exceptions prevent Redis calls."""
        mock_client = Mock()
        parser = MockParser(raise_error=MetricExpressionParseError("Bad expression"))
        validator = SchemaValidator(mock_client, parser)

        result = validator.validate("ns", "bad expression")

        assert result.is_valid is False
        mock_client.is_valid_metric_name.assert_not_called()
        mock_client.get_metric_names.assert_not_called()

    def test_empty_expression_success(self, metadata_client):
        """Test that empty expression returns success without Redis interaction."""
        mock_client = Mock()
        parser = MockParser()
        validator = SchemaValidator(mock_client, parser)

        result = validator.validate("ns", "")

        assert result.is_valid is True
        assert parser.parse_called is False
        mock_client.is_valid_metric_name.assert_not_called()

    def test_whitespace_expression_success(self, metadata_client):
        """Test that whitespace-only expression returns success."""
        mock_client = Mock()
        parser = MockParser()
        validator = SchemaValidator(mock_client, parser)

        result = validator.validate("ns", "   \t\n  ")

        assert result.is_valid is True
        assert parser.parse_called is False

    def test_none_expression_success(self, metadata_client):
        """Test that None expression returns success."""
        mock_client = Mock()
        parser = MockParser()
        validator = SchemaValidator(mock_client, parser)

        result = validator.validate("ns", None)

        assert result.is_valid is True

    def test_none_namespace_error(self, metadata_client):
        """Test that None namespace returns error."""
        parser = MockParser(return_value={"metric1"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(None, "metric1")

        assert result.is_valid is False
        assert "Namespace cannot be None" in result.error

    def test_empty_parser_result_success(self, metadata_client):
        """Test that parser returning empty set returns success."""
        mock_client = Mock()
        parser = MockParser(return_value=set())
        validator = SchemaValidator(mock_client, parser)

        result = validator.validate("ns", "some expression with no metrics")

        assert result.is_valid is True
        mock_client.is_valid_metric_name.assert_not_called()

    def test_bulk_optimization_below_threshold(self, metadata_client):
        """Test individual lookups used when below threshold."""
        namespace = "test_ns"
        metrics = {"m1", "m2", "m3"}
        metadata_client.set_metric_names(namespace, metrics)

        mock_client = Mock()
        mock_client.is_valid_metric_name.return_value = True

        parser = MockParser(return_value={"m1", "m2", "m3"})  # 3 metrics, below default 5
        validator = SchemaValidator(mock_client, parser, bulk_fetch_threshold=5)

        validator.validate(namespace, "expression")

        # Should call is_valid_metric_name for each metric
        assert mock_client.is_valid_metric_name.call_count == 3
        mock_client.get_metric_names.assert_not_called()

    def test_bulk_optimization_at_threshold(self, metadata_client):
        """Test bulk fetch used when at threshold."""
        namespace = "test_ns"
        metrics = {"m1", "m2", "m3", "m4", "m5"}
        metadata_client.set_metric_names(namespace, metrics)

        mock_client = Mock()
        mock_client.get_metric_names.return_value = metrics

        parser = MockParser(return_value=metrics)  # 5 metrics, at threshold
        validator = SchemaValidator(mock_client, parser, bulk_fetch_threshold=5)

        validator.validate(namespace, "expression")

        # Should call get_metric_names once
        mock_client.get_metric_names.assert_called_once_with(namespace)
        mock_client.is_valid_metric_name.assert_not_called()

    def test_bulk_optimization_above_threshold(self, metadata_client):
        """Test bulk fetch used when above threshold."""
        namespace = "test_ns"
        metrics = {f"metric{i}" for i in range(10)}
        metadata_client.set_metric_names(namespace, metrics)

        mock_client = Mock()
        mock_client.get_metric_names.return_value = metrics

        parser = MockParser(return_value=metrics)
        validator = SchemaValidator(mock_client, parser, bulk_fetch_threshold=5)

        validator.validate(namespace, "expression")

        mock_client.get_metric_names.assert_called_once()
        mock_client.is_valid_metric_name.assert_not_called()

    def test_bulk_optimization_finds_invalid(self, metadata_client):
        """Test bulk fetch correctly identifies invalid metrics."""
        namespace = "test_ns"
        valid_metrics = {"m1", "m2", "m3", "m4", "m5"}
        requested_metrics = {"m1", "m2", "m3", "invalid1", "invalid2"}

        mock_client = Mock()
        mock_client.get_metric_names.return_value = valid_metrics

        parser = MockParser(return_value=requested_metrics)
        validator = SchemaValidator(mock_client, parser, bulk_fetch_threshold=5)

        result = validator.validate(namespace, "expression")

        assert result.is_valid is False
        assert "invalid1" in result.invalid_metrics
        assert "invalid2" in result.invalid_metrics
        assert "m1" not in result.invalid_metrics

    def test_namespace_isolation(self, metadata_client):
        """Test that validation is isolated per namespace."""
        ns1 = "namespace1"
        ns2 = "namespace2"
        metadata_client.set_metric_names(ns1, {"metric_a", "metric_b"})
        metadata_client.set_metric_names(ns2, {"metric_x", "metric_y"})

        parser = MockParser(return_value={"metric_a"})
        validator = SchemaValidator(metadata_client, parser)

        # metric_a exists in ns1
        result1 = validator.validate(ns1, "expr")
        assert result1.is_valid is True

        # metric_a does NOT exist in ns2
        result2 = validator.validate(ns2, "expr")
        assert result2.is_valid is False
        assert "metric_a" in result2.invalid_metrics

    def test_duplicate_metrics_in_expression(self, metadata_client):
        """Test that duplicate metrics are deduplicated."""
        namespace = "test_ns"
        metadata_client.set_metric_names(namespace, {"metric1"})

        # Parser returns duplicates (as a set, but validator still deduplicates)
        mock_client = Mock()
        mock_client.is_valid_metric_name.return_value = True

        parser = MockParser(return_value={"metric1"})
        validator = SchemaValidator(mock_client, parser, bulk_fetch_threshold=10)

        validator.validate(namespace, "metric1 + metric1")

        # Should only check once due to set deduplication
        assert mock_client.is_valid_metric_name.call_count == 1

    def test_invalid_metrics_sorted_in_result(self, metadata_client):
        """Test that invalid metrics are sorted in the result."""
        namespace = "test_ns"
        metadata_client.set_metric_names(namespace, set())

        parser = MockParser(return_value={"zebra", "apple", "mango"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "expr")

        assert result.invalid_metrics == ["apple", "mango", "zebra"]

    def test_unicode_metric_names(self, metadata_client):
        """Test handling of unicode metric names."""
        namespace = "test_ns"
        metrics = {"cpu_usage", "memory_bytes"}
        metadata_client.set_metric_names(namespace, metrics)

        parser = MockParser(return_value={"cpu_usage", "memory_bytes"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "expr")

        assert result.is_valid is True

    def test_empty_string_namespace(self, metadata_client):
        """Test validation with empty string namespace."""
        namespace = ""
        metadata_client.set_metric_names(namespace, {"metric1"})

        parser = MockParser(return_value={"metric1"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "metric1")

        assert result.is_valid is True

    def test_special_characters_in_namespace(self, metadata_client):
        """Test validation with special characters in namespace."""
        namespace = "prod:app1:service"
        metadata_client.set_metric_names(namespace, {"metric1"})

        parser = MockParser(return_value={"metric1"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "metric1")

        assert result.is_valid is True


class TestSchemaValidatorIntegration:
    """Integration tests using real fakeredis."""

    def test_full_validation_flow(self, metadata_client):
        """Test complete validation flow with fakeredis."""
        namespace = "integration_test"
        valid_metrics = {"cpu.usage", "memory.total", "disk.read", "disk.write", "network.in"}
        metadata_client.set_metric_names(namespace, valid_metrics)

        # Test with subset of valid metrics
        parser = MockParser(return_value={"cpu.usage", "memory.total"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "cpu.usage + memory.total")
        assert result.is_valid is True

        # Test with mix of valid and invalid
        parser2 = MockParser(return_value={"cpu.usage", "invalid.metric"})
        validator2 = SchemaValidator(metadata_client, parser2)

        result2 = validator2.validate(namespace, "expr")
        assert result2.is_valid is False
        assert result2.invalid_metrics == ["invalid.metric"]

    def test_bulk_threshold_configuration(self, metadata_client):
        """Test configurable bulk fetch threshold."""
        namespace = "test"
        metrics = {f"m{i}" for i in range(20)}
        metadata_client.set_metric_names(namespace, metrics)

        # With low threshold, should use bulk
        parser = MockParser(return_value={f"m{i}" for i in range(10)})
        validator = SchemaValidator(metadata_client, parser, bulk_fetch_threshold=3)

        result = validator.validate(namespace, "expr")
        assert result.is_valid is True

        # With high threshold, should use individual
        validator2 = SchemaValidator(metadata_client, parser, bulk_fetch_threshold=100)
        result2 = validator2.validate(namespace, "expr")
        assert result2.is_valid is True

    def test_nonexistent_namespace(self, metadata_client):
        """Test validation against non-existent namespace."""
        parser = MockParser(return_value={"metric1"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate("nonexistent_namespace", "metric1")

        assert result.is_valid is False
        assert "metric1" in result.invalid_metrics


class TestSchemaValidatorWithPydanticAIParser:
    """
    Tests for SchemaValidator with PydanticAI-style parser stubs.

    These tests simulate the behavior of PydanticAIMetricExpressionParser
    to verify integration with SchemaValidator, including:
    - Parser returning deduplicated, normalized metrics
    - Parser confidence handling
    - Parser error propagation
    - Mixed case and duplicate handling
    """

    def test_parser_dedupe_with_redis_validation(self, metadata_client):
        """Test that parser deduplication works correctly with Redis validation."""
        namespace = "test_ns"
        valid_metrics = {"cpu.usage", "memory.total"}
        metadata_client.set_metric_names(namespace, valid_metrics)

        # Parser returns metrics with duplicates (like LLM might)
        parser = MockParser(return_value={"cpu.usage", "cpu.usage", "memory.total"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "cpu.usage + cpu.usage + memory.total")

        assert result.is_valid is True

    def test_parser_mixed_case_normalized(self, metadata_client):
        """Test that mixed-case metrics from parser match lowercase Redis keys."""
        namespace = "test_ns"
        # Redis stores lowercase
        metadata_client.set_metric_names(namespace, {"cpu.usage", "memory.total"})

        # Simulate parser that normalizes to lowercase (like PydanticAI parser does)
        parser = MockParser(return_value={"cpu.usage", "memory.total"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "CPU.Usage + MEMORY.Total")

        assert result.is_valid is True

    def test_parser_confidence_low_but_valid_metrics(self, metadata_client):
        """Test validation succeeds even with low confidence if metrics are valid."""
        namespace = "test_ns"
        valid_metrics = {"cpu.usage"}
        metadata_client.set_metric_names(namespace, valid_metrics)

        # Parser returns valid metrics (confidence is parser-internal)
        parser = MockParser(return_value={"cpu.usage"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "ambiguous expression")

        assert result.is_valid is True

    def test_parser_empty_result_expression_with_only_functions(self, metadata_client):
        """Test that expression with only functions (no metrics) is valid."""
        namespace = "test_ns"
        metadata_client.set_metric_names(namespace, {"some.metric"})

        # Parser found no metrics (expression was all functions/numbers)
        parser = MockParser(return_value=set())
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "100 + 200 / 2")

        assert result.is_valid is True

    def test_parser_invalid_metrics_sorted_alphabetically(self, metadata_client):
        """Test that invalid metrics are returned sorted for consistent output."""
        namespace = "test_ns"
        metadata_client.set_metric_names(namespace, set())

        parser = MockParser(return_value={"zebra.metric", "alpha.metric", "middle.metric"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "expr")

        assert result.is_valid is False
        assert result.invalid_metrics == ["alpha.metric", "middle.metric", "zebra.metric"]

    def test_parser_partial_match_some_valid_some_invalid(self, metadata_client):
        """Test partial validation when some metrics exist and some don't."""
        namespace = "test_ns"
        metadata_client.set_metric_names(namespace, {"cpu.usage", "memory.total"})

        parser = MockParser(return_value={"cpu.usage", "memory.total", "disk.io", "network.bytes"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "complex expression")

        assert result.is_valid is False
        assert len(result.invalid_metrics) == 2
        assert "disk.io" in result.invalid_metrics
        assert "network.bytes" in result.invalid_metrics
        assert "cpu.usage" not in result.invalid_metrics

    def test_parser_error_includes_original_message(self, metadata_client):
        """Test that parser error message is included in validation result."""
        parser = MockParser(raise_error=MetricExpressionParseError("Invalid syntax at position 10"))
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate("ns", "bad expression")

        assert result.is_valid is False
        assert "Invalid syntax at position 10" in result.error

    def test_parser_generic_exception_wrapped(self, metadata_client):
        """Test that generic parser exceptions are wrapped properly."""
        parser = MockParser(raise_error=RuntimeError("Unexpected LLM failure"))
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate("ns", "expression")

        assert result.is_valid is False
        assert "Unexpected parser error" in result.error
        assert "Unexpected LLM failure" in result.error

    def test_parser_timeout_error_handled(self, metadata_client):
        """Test that timeout errors from parser are handled gracefully."""
        parser = MockParser(raise_error=TimeoutError("OpenAI request timed out"))
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate("ns", "expression")

        assert result.is_valid is False
        assert "Unexpected parser error" in result.error

    def test_multiple_validations_same_validator(self, metadata_client):
        """Test that validator can be reused for multiple validations."""
        ns1 = "namespace1"
        ns2 = "namespace2"
        metadata_client.set_metric_names(ns1, {"metric.a", "metric.b"})
        metadata_client.set_metric_names(ns2, {"metric.x", "metric.y"})

        parser = MockParser(return_value={"metric.a"})
        validator = SchemaValidator(metadata_client, parser)

        # First validation - should pass in ns1
        result1 = validator.validate(ns1, "expr")
        assert result1.is_valid is True

        # Second validation - should fail in ns2 (metric.a not in ns2)
        result2 = validator.validate(ns2, "expr")
        assert result2.is_valid is False

    def test_error_message_includes_namespace(self, metadata_client):
        """Test that error message includes namespace for context."""
        namespace = "production_metrics"
        metadata_client.set_metric_names(namespace, set())

        parser = MockParser(return_value={"invalid.metric"})
        validator = SchemaValidator(metadata_client, parser)

        result = validator.validate(namespace, "expr")

        assert result.is_valid is False
        assert "production_metrics" in result.error

    def test_bulk_vs_individual_validation_consistency(self, metadata_client):
        """Test that bulk and individual validation produce same results."""
        namespace = "test_ns"
        valid_metrics = {f"metric{i}" for i in range(10)}
        invalid_metrics = {"bad.metric1", "bad.metric2"}
        metadata_client.set_metric_names(namespace, valid_metrics)

        # Request mix of valid and invalid
        requested = valid_metrics | invalid_metrics

        # Below bulk threshold (individual validation)
        parser = MockParser(return_value=requested)
        validator_individual = SchemaValidator(metadata_client, parser, bulk_fetch_threshold=20)
        result_individual = validator_individual.validate(namespace, "expr")

        # Above bulk threshold (bulk validation)
        validator_bulk = SchemaValidator(metadata_client, parser, bulk_fetch_threshold=5)
        result_bulk = validator_bulk.validate(namespace, "expr")

        # Results should be consistent
        assert result_individual.is_valid == result_bulk.is_valid
        assert set(result_individual.invalid_metrics) == set(result_bulk.invalid_metrics)
