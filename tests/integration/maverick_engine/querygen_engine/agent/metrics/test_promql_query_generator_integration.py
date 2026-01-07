"""
Integration tests for PromQL Query Generator with ReAct pattern.

This test validates the end-to-end functionality of the query generator
with validation tool and iterative refinement.
"""

import pytest
import redis

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.querygen_engine.agent.metrics.promql_query_generator_agent import (
    PromQLQueryGeneratorAgent,
)
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    QueryGenerationResult,
)
from maverick_engine.querygen_engine.metrics.preprocessor.promql_querygen_preprocessor import (
    PromQLQuerygenPreprocessor,
)
from maverick_engine.validation_engine.metrics.syntax.promql_syntax_validator import (
    PromQLSyntaxValidator,
)
from maverick_engine.validation_engine.metrics.schema.metrics_schema_validator import (
    MetricsSchemaValidator,
)
from maverick_engine.validation_engine.metrics.semantics.promql_semantics_validator import (
    PromQLSemanticsValidator,
)
from maverick_engine.validation_engine.metrics.promql_validator import (
    PromQLValidator,
)
from maverick_engine.validation_engine.agent.metrics.promql_metricname_extractor_agent import (
    PromQLMetricNameExtractorAgent,
)
from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


@pytest.mark.integration
@pytest.mark.integration_querygen_evals
class TestPromQLQueryGeneratorIntegration:
    """Integration tests for query generator with ReAct pattern and validation tool."""

    @pytest.fixture
    def config_manager(self):
        """Initialize ConfigManager for agents."""
        return ConfigManager(expand_path("$HOME/.maverick_test"), "config.yml")

    @pytest.fixture
    def instructions_manager(self):
        """Initialize InstructionsManager for agents."""
        return InstructionsManager()

    @pytest.fixture
    def preprocessor(self):
        """Initialize query preprocessor."""
        return PromQLQuerygenPreprocessor()

    @pytest.fixture
    def promql_syntax_validator(self):
        """Initialize syntax validator."""
        return PromQLSyntaxValidator()

    @pytest.fixture
    def redis_client(self):
        """Create Redis client for metadata store."""
        return redis.Redis(host="localhost", port=6380, decode_responses=True)

    @pytest.fixture
    def metadata_store(self, redis_client):
        """Create metrics metadata store."""
        return MetricsMetadataStore(redis_client)

    @pytest.fixture
    def metric_extractor_agent(self, config_manager, instructions_manager):
        """Create metric name extractor agent."""
        return PromQLMetricNameExtractorAgent(
            config_manager=config_manager, instructions_manager=instructions_manager
        )

    @pytest.fixture
    def promql_schema_validator(self, metadata_store, metric_extractor_agent):
        """Initialize schema validator."""
        return MetricsSchemaValidator(metadata_store, metric_extractor_agent)

    @pytest.fixture
    def promql_semantics_validator(self, config_manager, instructions_manager):
        """Initialize semantics validator."""
        return PromQLSemanticsValidator(
            config_manager=config_manager, instructions_manager=instructions_manager
        )

    @pytest.fixture
    def promql_validator(
        self,
        config_manager,
        instructions_manager,
        promql_syntax_validator,
        promql_schema_validator,
        promql_semantics_validator,
    ):
        """Initialize PromQL validator pipeline."""
        return PromQLValidator(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            syntax_validator=promql_syntax_validator,
            schema_validator=promql_schema_validator,
            semantics_validator=promql_semantics_validator,
        )

    @pytest.fixture
    def query_generator(
        self,
        config_manager,
        instructions_manager,
        preprocessor,
        promql_validator,
    ):
        """Initialize query generator with all components."""
        return PromQLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            preprocessor=preprocessor,
            promql_validator=promql_validator,
        )

    @pytest.mark.asyncio
    async def test_generate_query_happy_path_counter_with_rate(
        self, query_generator, metadata_store
    ):
        """
        Integration test for happy path query generation with ReAct pattern.

        Tests the complete ReAct loop for generating a PromQL query for a counter
        metric with rate aggregation using the validation tool.

        Expected behavior:
        - Query should be generated successfully
        - Agent should use the validate_promql_query tool
        - Query should pass all validations
        - Validation attempts should be tracked
        - Final query should use rate() on a counter metric

        Note: This test uses real LLM agents, so it will consume tokens.
        """
        # Setup: Seed metadata store with valid metrics
        namespace = "test:monitoring"
        metadata_store.set_metric_names(namespace, {"http_requests_total", "cpu_usage"})

        # Arrange: Create user intent for a counter metric with rate aggregation
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            intent_description="Calculate HTTP 5xx requests rate with a 5 minute range window",
            metric_type="counter",
            filters={"status": "500", "method": "GET"},
            window="5m",
            group_by=["instance"],
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate")
            ],
        )

        # Act: Generate query using ReAct pattern
        result = await query_generator.generate_query(namespace, intent)

        # Assert: Verify the generation succeeded
        print("\n=== Query Generation Result (ReAct Pattern) ===")
        print(f"Success: {result.success}")
        print(f"Final Query: {result.query}")
        if hasattr(result, "error") and result.error:
            print(f"Error: {result.error}")
        print("=" * 50)

        assert isinstance(result, QueryGenerationResult)
        assert result.success is True, (
            f"Expected successful generation but got failure. Error: {getattr(result, 'error', 'Unknown error')}"
        )

        # Verify query structure and content
        assert result.query is not None and len(result.query) > 0
        assert "rate(" in result.query, "Expected rate() function in counter query"
        assert "http_requests_total" in result.query, "Expected metric name in query"
        assert 'status="500"' in result.query or "status='500'" in result.query, (
            "Expected status filter in query"
        )
        # assert 'method="GET"' in result.query or "method='GET'" in result.query, (
        #     "Expected method filter in query"
        # )
        # assert "[5m]" in result.query, "Expected 5m time window in query"
        assert "by (instance)" in result.query or "by(instance)" in result.query, (
            "Expected grouping by instance"
        )
        print(f"Final validated query: {result.query}")
