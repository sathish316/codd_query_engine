"""
Integration tests for PromQL Query Explainer Agent and Semantic Validator.
"""

import pytest

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.validation_engine.agent.metrics.promql_query_explainer_agent import (
    PromQLQueryExplainerAgent,
)
from maverick_engine.validation_engine.metrics.semantics.structured_outputs import (
    SemanticValidationResult,
)
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


@pytest.mark.integration
@pytest.mark.integration_llm
class TestPromQLQueryExplainerAgentIntegration:
    @pytest.fixture
    def query_explainer_agent(self):
        """Initialize the PromQL Query Explainer Agent with real dependencies."""
        config_manager = ConfigManager(
            expand_path("$HOME/.maverick_test"), "config.yml"
        )
        instructions_manager = InstructionsManager()
        return PromQLQueryExplainerAgent(
            config_manager=config_manager, instructions_manager=instructions_manager
        )

    def test_semantic_validation_happy_path_counter_with_rate(
        self, query_explainer_agent: PromQLQueryExplainerAgent
    ):
        """
        Integration test for the happy path of query explainer agent and semantic validator.

        Tests a counter metric with rate aggregation, which is the most common and
        straightforward scenario for semantic validation.

        Expected behavior:
        - is_valid should be True (query matches user intent)
        - Confidence score should be high (>2)
        - Reasoning should confirm correct usage of rate() on counter metric
        """
        # Arrange: Create user intent for a counter metric with rate aggregation
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            meter_type="counter",
            filters={"status": "500"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate")
            ],
        )

        # Generated PromQL query that matches the intent
        generated_query = 'rate(http_requests_total{status="500"}[5m])'

        # Act: Validate semantic match between intent and generated query
        result = query_explainer_agent.validate_semantic_match(intent, generated_query)

        print("semantic validation result: ", result)
        # Assert: Verify the validation result indicates a full match
        assert isinstance(result, SemanticValidationResult)
        assert result.is_valid is True, (
            f"Expected is_valid=True but got False. "
            f"Reasoning: {result.reasoning}"
        )
        assert result.confidence_score > 2, f"Expected confidence score > 2 but got {result.confidence_score}"
        assert result.reasoning is not None and len(result.reasoning) > 0

    def test_semantic_validation_intent_mismatch(self, query_explainer_agent: PromQLQueryExplainerAgent):
        """
        Integration test for semantic validation when intent does NOT match the generated query.

        Tests a scenario where the user wants to calculate average memory usage (gauge metric)
        but the generated query incorrectly uses rate() which is for counter metrics.

        Expected behavior:
        - is_valid should be False (query doesn't match user intent)
        - Confidence score should be low (<=2)
        - Reasoning should identify the mismatch
        """
        # Arrange: Create user intent for a gauge metric with avg_over_time aggregation
        intent = MetricsQueryIntent(
            metric="memory_usage_bytes",
            meter_type="gauge",
            filters={"instance": "prod-server-1"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="avg_over_time")
            ],
        )

        # Generated query that INCORRECTLY uses rate() on a gauge metric
        # This is semantically wrong - rate() should be used for counters, not gauges
        generated_query = 'rate(memory_usage_bytes{instance="prod-server-1"}[5m])'

        # Act: Validate semantic match between intent and generated query
        result = query_explainer_agent.validate_semantic_match(intent, generated_query)

        # Assert: Verify the validation result indicates a mismatch
        print("semantic validation result: ", result)
        assert isinstance(result, SemanticValidationResult)
        assert result.is_valid is False, (
            f"Expected is_valid=False for mismatched query but got True. "
            f"Reasoning: {result.reasoning}"
        )
        assert result.confidence_score <= 2, f"Expected confidence score < 2 but got {result.confidence_score}"
        assert result.reasoning is not None and len(result.reasoning) > 0
