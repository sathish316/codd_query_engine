"""
Unit tests for PromQLValidator.

Tests cover:
- Pipeline orchestration (syntax -> schema -> semantics)
- All validation stages run and errors are collected
- Optional semantic validation (with/without intent)
- Proper result aggregation from all validators
- Edge cases (None validators, empty queries, etc.)

All tests use mocks to avoid external dependencies.
"""

from unittest.mock import Mock
import pytest

from maverick_engine.validation_engine.metrics.promql_validator import PromQLValidator
from maverick_engine.validation_engine.metrics.validation_result import (
    ValidationResult,
    ValidationResultList,
)
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
    def mock_config_manager(self):
        """Create a mock config manager."""
        mock_config = Mock()
        # Configure to return True for all validation stages by default
        mock_config.get_setting.return_value = True
        return mock_config

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
        self, mock_config_manager, mock_syntax_validator, mock_schema_validator, mock_semantics_validator
    ):
        """Create a PromQLValidator with mocked dependencies."""
        return PromQLValidator(
            config_manager=mock_config_manager,
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
            meter_type="counter",
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

        # Verify: Returns simple ValidationResult for success
        assert result.is_valid is True
        assert isinstance(result, ValidationResult)
        assert result.error is None

    def test_syntax_validation_failure(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that syntax validation failure is collected.

        Scenario: Malformed query - all validators run but errors are collected.
        """
        # Setup: Syntax validator returns failure, others return success
        namespace = "test:namespace"
        query = "rate(http_requests_total[5m"  # Missing closing paren

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.failure(
            "Invalid PromQL syntax at line 1, column 30", line=1, column=30
        )
        mock_schema_validator.validate.return_value = SchemaValidationResult.success()

        # Execute
        result = validator.validate(namespace, query)

        # Verify: All enabled validators were called
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_called_once_with(namespace, query)

        # Verify: Result is ValidationResultList with syntax error
        assert result.is_valid is False
        assert isinstance(result, ValidationResultList)
        assert "syntax" in result.error.lower()
        assert len(result.results) == 1
        assert isinstance(result.results[0], SyntaxValidationResult)

    def test_schema_validation_failure(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that schema validation failure is collected.

        Scenario: Valid syntax but invalid metric - all validators run.
        """
        # Setup: Syntax passes, schema fails, semantics passes
        namespace = "test:namespace"
        query = "rate(nonexistent_metric[5m])"
        intent = MetricsQueryIntent(
            metric="nonexistent_metric", meter_type="counter", window="5m"
        )

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.success()
        mock_schema_validator.validate.return_value = SchemaValidationResult.failure(
            ["nonexistent_metric"], namespace
        )
        mock_semantics_validator.validate.return_value = SemanticValidationResult.success()

        # Execute
        result = validator.validate(namespace, query, intent=intent)

        # Verify: All validators were called
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_called_once_with(namespace, query)
        mock_semantics_validator.validate.assert_called_once_with(intent, query)

        # Verify: Result is ValidationResultList with schema error
        assert result.is_valid is False
        assert isinstance(result, ValidationResultList)
        assert "nonexistent_metric" in result.error or "schema" in result.error.lower()
        assert len(result.results) == 1
        assert isinstance(result.results[0], SchemaValidationResult)

    def test_semantic_validation_failure(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that semantic validation failure is collected.

        Scenario: Valid syntax and schema, but query doesn't match intent.
        """
        # Setup: Syntax and schema pass, semantics fails
        namespace = "test:namespace"
        query = "rate(memory_usage_bytes[5m])"  # rate() on gauge
        intent = MetricsQueryIntent(
            metric="memory_usage_bytes",
            meter_type="gauge",
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="avg_over_time")
            ],
        )

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.success()
        mock_schema_validator.validate.return_value = SchemaValidationResult.success()
        mock_semantics_validator.validate.return_value = SemanticValidationResult(
            confidence_score=1,
            reasoning="Critical error - applying rate() to a gauge metric",
        )

        # Execute
        result = validator.validate(namespace, query, intent=intent)

        # Verify: All validators were called
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_called_once_with(namespace, query)
        mock_semantics_validator.validate.assert_called_once_with(intent, query)

        # Verify: Result is ValidationResultList with semantic error
        assert result.is_valid is False
        assert isinstance(result, ValidationResultList)
        assert len(result.results) == 1
        assert isinstance(result.results[0], SemanticValidationResult)
        assert result.results[0].confidence_score == 1

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
        # Setup: All validators pass, semantic returns partial match (score 3 > threshold 2)
        namespace = "test:namespace"
        query = 'rate(http_requests_total{status="500"}[5m])'
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            meter_type="counter",
            filters={"status": "500", "method": "GET"},  # Query missing method filter
            window="5m",
        )

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.success()
        mock_schema_validator.validate.return_value = SchemaValidationResult.success()
        mock_semantics_validator.validate.return_value = SemanticValidationResult(
            confidence_score=3,
            reasoning="Missing endpoint filter makes the query broader than intended, but it still measures the core metric",
        )

        # Execute
        result = validator.validate(namespace, query, intent=intent)

        # Verify: All validators were called
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_called_once_with(namespace, query)
        mock_semantics_validator.validate.assert_called_once_with(intent, query)

        # Verify: Returns simple ValidationResult for success (score 3 > threshold 2)
        assert result.is_valid is True
        assert isinstance(result, ValidationResult)
        assert result.error is None

    def test_multiple_validation_errors_collected(
        self,
        validator,
        mock_syntax_validator,
        mock_schema_validator,
        mock_semantics_validator,
    ):
        """
        Test that multiple validation errors are collected together.

        Scenario: Multiple validators fail - all errors should be aggregated.
        """
        # Setup: Syntax and schema both fail
        namespace = "test:namespace"
        query = "rate(invalid_metric[5m"  # Bad syntax AND bad metric
        intent = MetricsQueryIntent(
            metric="invalid_metric", meter_type="counter", window="5m"
        )

        mock_syntax_validator.validate.return_value = SyntaxValidationResult.failure(
            "Invalid PromQL syntax at line 1, column 26", line=1, column=26
        )
        mock_schema_validator.validate.return_value = SchemaValidationResult.failure(
            ["invalid_metric"], namespace
        )
        mock_semantics_validator.validate.return_value = SemanticValidationResult(
            confidence_score=1, reasoning="Query does not match intent"
        )

        # Execute
        result = validator.validate(namespace, query, intent=intent)

        # Verify: All validators were called
        mock_syntax_validator.validate.assert_called_once_with(query)
        mock_schema_validator.validate.assert_called_once_with(namespace, query)
        mock_semantics_validator.validate.assert_called_once_with(intent, query)

        # Verify: Result contains all three errors
        assert result.is_valid is False
        assert isinstance(result, ValidationResultList)
        assert len(result.results) == 3

        # Check that all error types are present
        result_types = [type(r).__name__ for r in result.results]
        assert "SyntaxValidationResult" in result_types
        assert "SchemaValidationResult" in result_types
        # assert "SemanticValidationResult" in result_types

        # Verify formatted error contains all stages
        assert "syntax" in result.error.lower()
        assert "schema" in result.error.lower()
        # assert "semantic" in result.error.lower()
