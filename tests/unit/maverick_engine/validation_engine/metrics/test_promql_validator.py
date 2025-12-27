"""
Unit tests for PromQLValidator.

Tests cover:
- Pipeline orchestration (syntax -> schema -> semantics)
- Early exit on validation failures at each stage
- Optional semantic validation (with/without intent)
- Proper result propagation from each validator
- Edge cases (None validators, empty queries, etc.)

All tests use mocks to avoid external dependencies.
"""

from unittest.mock import Mock
import pytest

from maverick_engine.validation_engine.metrics.promql_validator import PromQLValidator
from maverick_engine.validation_engine.metrics.syntax.structured_outputs import (
    SyntaxValidationResult,
)
from maverick_engine.validation_engine.metrics.schema.structured_outputs import (
    SchemaValidationResult,
)
from maverick_engine.validation_engine.metrics.semantics.structured_outputs import (
    SemanticValidationResult,
)
from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)


class TestPromQLValidator:
    """Test suite for PromQLValidator pipeline."""

    @pytest.fixture
    def mock_syntax_validator(self):
        """Create a mock syntax validator."""
        return Mock()

    @pytest.fixture
    def mock_schema_validator(self):
        """Create a mock schema validator."""
        return Mock()

    @pytest.fixture
    def mock_semantics_validator(self):
        """Create a mock semantics validator."""
        return Mock()

    @pytest.fixture
    def validator(
        self, mock_syntax_validator, mock_schema_validator, mock_semantics_validator
    ):
        """Create a PromQLValidator with mocked dependencies."""
        return PromQLValidator(
            syntax_validator=mock_syntax_validator,
            schema_validator=mock_schema_validator,
            semantics_validator=mock_semantics_validator,
        )

    def test_all_stages_pass_with_intent(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that all three validation stages execute when all pass.

        Scenario: Valid query with intent provided - all validators should be called.
        """
        # Setup: All validators return success
        namespace = "test:namespace"
        query = "rate(http_requests_total[5m])"
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate")
            ],
        )

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.success()
        mock_schema_validator.validate.return_value = SchemaValidationResult.success()
        mock_semantics_validator.validate.return_value = (
            SemanticValidationResult.success()
        )

        # Execute
        result = validator.validate(namespace, query, intent=intent)

        # Verify: All validators were called in order
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_called_once_with(namespace, query)
        mock_semantics_validator.validate.assert_called_once_with(intent, query)

        # Verify: Final result is from semantic validation
        assert result.is_valid is True
        assert isinstance(result, SemanticValidationResult)
        assert result.intent_match is True

    def test_syntax_validation_failure_stops_pipeline(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that pipeline stops at syntax validation failure.

        Scenario: Malformed query - schema and semantic validation should not run.
        """
        # Setup: Syntax validator returns failure
        namespace = "test:namespace"
        query = "rate(http_requests_total[5m"  # Missing closing paren

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.failure(
            "Invalid PromQL syntax at line 1, column 30", line=1, column=30
        )

        # Execute
        result = validator.validate(namespace, query)

        # Verify: Only syntax validator was called
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_not_called()
        mock_semantics_validator.validate.assert_not_called()

        # Verify: Result is syntax validation failure
        assert result.is_valid is False
        assert isinstance(result, SyntaxValidationResult)
        assert "syntax" in result.error.lower()
        assert result.line == 1
        assert result.column == 30

    def test_schema_validation_failure_stops_pipeline(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that pipeline stops at schema validation failure.

        Scenario: Valid syntax but invalid metric - semantic validation should not run.
        """
        # Setup: Syntax passes, schema fails
        namespace = "test:namespace"
        query = "rate(nonexistent_metric[5m])"
        intent = MetricsQueryIntent(
            metric="nonexistent_metric", metric_type="counter", window="5m"
        )

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.success()
        mock_schema_validator.validate.return_value = SchemaValidationResult.failure(
            ["nonexistent_metric"], namespace
        )

        # Execute
        result = validator.validate(namespace, query, intent=intent)

        # Verify: Syntax and schema validators called, but not semantics
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_called_once_with(namespace, query)
        mock_semantics_validator.validate.assert_not_called()

        # Verify: Result is schema validation failure
        assert result.is_valid is False
        assert isinstance(result, SchemaValidationResult)
        assert "nonexistent_metric" in result.invalid_metrics
        assert namespace in result.error

    def test_semantic_validation_failure(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that semantic validation failure is properly returned.

        Scenario: Valid syntax and schema, but query doesn't match intent.
        """
        # Setup: Syntax and schema pass, semantics fails
        namespace = "test:namespace"
        query = "rate(memory_usage_bytes[5m])"  # rate() on gauge
        intent = MetricsQueryIntent(
            metric="memory_usage_bytes",
            metric_type="gauge",
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="avg_over_time")
            ],
        )

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.success()
        mock_schema_validator.validate.return_value = SchemaValidationResult.success()
        mock_semantics_validator.validate.return_value = SemanticValidationResult(
            intent_match=False,
            partial_match=False,
            explanation="rate() should not be used on gauge metrics",
            original_intent_summary="Average of gauge over time",
            actual_query_behavior="Rate calculation on gauge",
        )

        # Execute
        result = validator.validate(namespace, query, intent=intent)

        # Verify: All validators were called
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_called_once_with(namespace, query)
        mock_semantics_validator.validate.assert_called_once_with(intent, query)

        # Verify: Result is semantic validation failure
        assert result.is_valid is False
        assert isinstance(result, SemanticValidationResult)
        assert result.intent_match is False
        assert "rate()" in result.explanation

    def test_partial_semantic_match(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that partial semantic match is handled correctly.

        Scenario: Query partially matches intent (is_valid should be True for partial match).
        """
        # Setup: All validators pass, semantic returns partial match
        namespace = "test:namespace"
        query = 'rate(http_requests_total{status="500"}[5m])'
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
            filters={"status": "500", "method": "GET"},  # Query missing method filter
            window="5m",
        )

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.success()
        mock_schema_validator.validate.return_value = SchemaValidationResult.success()
        mock_semantics_validator.validate.return_value = SemanticValidationResult(
            intent_match=False,
            partial_match=True,  # Partial match
            explanation="Query matches metric and some filters, but missing method filter",
            original_intent_summary="Rate with status and method filters",
            actual_query_behavior="Rate with only status filter",
        )

        # Execute
        result = validator.validate(namespace, query, intent=intent)

        # Verify: Result shows partial match
        assert result.is_valid is True  # Partial match counts as valid
        assert isinstance(result, SemanticValidationResult)
        assert result.intent_match is False
        assert result.partial_match is True
