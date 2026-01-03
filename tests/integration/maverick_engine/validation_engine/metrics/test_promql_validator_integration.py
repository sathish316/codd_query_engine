"""
Integration tests for the complete PromQL validator pipeline.

Tests the end-to-end validation flow through PromQLValidator which chains:
1. Syntax validation (PromQLSyntaxValidator)
2. Schema validation (MetricsSchemaValidator)
3. Semantic validation (PromQLSemanticsValidator)
"""

import pytest
import redis

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.validation_engine.agent.metrics.promql_metricname_extractor_agent import (
    PromQLMetricNameExtractorAgent,
)
from maverick_engine.validation_engine.metrics.promql_validator import PromQLValidator
from maverick_engine.validation_engine.metrics.schema.metrics_schema_validator import (
    MetricsSchemaValidator,
)
from maverick_engine.validation_engine.metrics.syntax.promql_syntax_validator import (
    PromQLSyntaxValidator,
)
from maverick_engine.validation_engine.metrics.semantics.promql_semantics_validator import (
    PromQLSemanticsValidator,
)
from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


@pytest.mark.integration
class TestPromQLValidatorPipelineIntegration:
    """Integration tests for the complete PromQL validation pipeline using PromQLValidator."""

    @pytest.fixture
    def config_manager(self):
        """Create ConfigManager with test configuration."""
        return ConfigManager(expand_path("$HOME/.maverick_test"), "config.yml")

    @pytest.fixture
    def instructions_manager(self):
        """Create InstructionsManager for loading prompts."""
        return InstructionsManager()

    @pytest.fixture
    def syntax_validator(self):
        """Create PromQL syntax validator."""
        return PromQLSyntaxValidator()

    @pytest.fixture
    def metric_extractor_agent(self, config_manager, instructions_manager):
        """Create metric name extractor agent."""
        return PromQLMetricNameExtractorAgent(
            config_manager=config_manager, instructions_manager=instructions_manager
        )

    @pytest.fixture
    def redis_client(self):
        """Create Redis client for metadata store."""
        return redis.Redis(host="localhost", port=6380, decode_responses=True)

    @pytest.fixture
    def metadata_store(self, redis_client):
        """Create metrics metadata store."""
        return MetricsMetadataStore(redis_client)

    @pytest.fixture
    def schema_validator(self, metadata_store, metric_extractor_agent):
        """Create schema validator with dependencies."""
        return MetricsSchemaValidator(metadata_store, metric_extractor_agent)

    @pytest.fixture
    def semantic_validator(self, config_manager, instructions_manager):
        """Create semantic validator (PromQL semantics validator)."""
        return PromQLSemanticsValidator(
            config_manager=config_manager, instructions_manager=instructions_manager
        )

    @pytest.fixture
    def promql_validator(
        self, config_manager, instructions_manager, syntax_validator, schema_validator, semantic_validator
    ):
        """Create the complete PromQL validator pipeline."""
        return PromQLValidator(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            syntax_validator=syntax_validator,
            schema_validator=schema_validator,
            semantics_validator=semantic_validator,
        )

    def test_validator_pipeline_happy_path(self, promql_validator, metadata_store):
        """
        Integration test for the complete validator pipeline - HAPPY PATH.

        Tests a valid PromQL query that passes all three validation stages:
        1. Syntax validation - Query is syntactically correct
        2. Schema validation - Metric exists in namespace
        3. Semantic validation - Query matches user intent

        Scenario: Counter metric with rate() aggregation - the canonical PromQL pattern
        """
        # Setup: Define test data
        namespace = "test:monitoring"
        query = 'rate(http_requests_total{status="500"}[5m])'

        # Seed metadata store with valid metrics
        metadata_store.set_metric_names(namespace, {"http_requests_total", "cpu_usage"})

        # Define user intent
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
            filters={"status": "500"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate")
            ],
        )

        # Execute validation through the complete pipeline
        result = promql_validator.validate(namespace, query, intent=intent)

        # Verify: All validations passed
        assert result.is_valid is True, f"Validation pipeline failed: {result.error}"

        # For semantic validation result, check specific fields
        assert hasattr(result, "intent_match"), "Expected SemanticValidationResult"
        assert result.intent_match is True, (
            f"Semantic validation failed. Intent did not match query. "
            f"Explanation: {result.explanation}"
        )
        assert result.explanation is not None
        assert result.original_intent_summary is not None
        assert result.actual_query_behavior is not None

    def test_validator_pipeline_syntax_error(self, promql_validator, metadata_store):
        """
        Integration test for validator pipeline - SYNTAX VALIDATION ERROR.

        Tests that a syntactically invalid query fails at the first stage
        and does not proceed to schema or semantic validation.

        Scenario: Malformed PromQL query with syntax error (incomplete expression)
        """
        # Setup: Malformed query with syntax error
        namespace = "test:monitoring"
        query = "rate(http_requests_total[5m"  # Missing closing parenthesis

        # Seed metadata store (should not be accessed due to syntax failure)
        metadata_store.set_metric_names(namespace, {"http_requests_total"})

        # Execute validation - should fail at syntax stage
        result = promql_validator.validate(namespace, query)

        # Verify: Syntax validation failed
        assert result.is_valid is False, (
            "Expected syntax validation to fail for malformed query"
        )
        assert result.error is not None
        assert "syntax" in result.error.lower() or "parser" in result.error.lower()

        # Verify it's a SyntaxValidationResult (has line/column info)
        assert hasattr(result, "line") or hasattr(result, "column"), (
            "Expected SyntaxValidationResult with error location"
        )

    def test_validator_pipeline_schema_error(self, promql_validator, metadata_store):
        """
        Integration test for validator pipeline - SCHEMA VALIDATION ERROR.

        Tests that a query with valid syntax but invalid metric names fails
        at the schema validation stage.

        Scenario: Query references a metric that doesn't exist in the namespace
        """
        # Setup: Valid syntax but metric doesn't exist
        namespace = "test:monitoring"
        query = 'rate(nonexistent_metric{status="500"}[5m])'

        # Seed metadata store with different metrics (not the one in query)
        metadata_store.set_metric_names(namespace, {"http_requests_total", "cpu_usage"})

        # Execute validation - should fail at schema stage
        result = promql_validator.validate(namespace, query)

        # Verify: Schema validation failed
        assert result.is_valid is False, (
            "Expected schema validation to fail for non-existent metric"
        )
        assert result.error is not None
        assert namespace in result.error

        # Verify it's a SchemaValidationResult (has invalid_metrics)
        assert hasattr(result, "invalid_metrics"), (
            "Expected SchemaValidationResult with invalid_metrics field"
        )
        assert "nonexistent_metric" in result.invalid_metrics, (
            f"Expected 'nonexistent_metric' in invalid_metrics, got: {result.invalid_metrics}"
        )

    def test_validator_pipeline_semantic_error(self, promql_validator, metadata_store):
        """
        Integration test for validator pipeline - SEMANTIC VALIDATION ERROR.

        Tests that a query with valid syntax and valid metrics but incorrect
        semantic usage fails at the semantic validation stage.

        Scenario: Using rate() on a gauge metric (semantically incorrect)
        """
        # Setup: Valid syntax, valid metric, but semantically wrong usage
        namespace = "test:monitoring"
        query = 'rate(memory_usage_bytes{instance="prod-1"}[5m])'

        # Seed metadata store with the metric
        metadata_store.set_metric_names(namespace, {"memory_usage_bytes"})

        # Define user intent: wants avg_over_time on gauge, but query uses rate()
        intent = MetricsQueryIntent(
            metric="memory_usage_bytes",
            metric_type="gauge",  # Gauge metric
            filters={"instance": "prod-1"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(
                    function_name="avg_over_time"
                )  # Expects avg_over_time
            ],
        )

        # Execute validation through the complete pipeline
        result = promql_validator.validate(namespace, query, intent=intent)

        # Verify: Semantic validation failed
        assert result.is_valid is False, (
            "Expected semantic validation to fail for incorrect aggregation usage. "
            "rate() should not be used on gauge metrics."
        )

        # Verify it's a SemanticValidationResult
        assert hasattr(result, "intent_match"), "Expected SemanticValidationResult"
        assert result.intent_match is False, (
            f"Expected intent_match to be False. Explanation: {result.explanation}"
        )
        assert result.explanation is not None
        # The explanation should mention the mismatch
        assert len(result.explanation) > 0
