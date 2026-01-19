"""
Unit tests for PromQL query explainer agent.
"""

import pytest
from unittest.mock import Mock
from dataclasses import dataclass

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.validation_engine.agent.metrics.promql_query_explainer_agent import (
    PromQLQueryExplainerAgent,
    SemanticValidationError,
    SemanticValidationResult,
)


@dataclass
class MockAgentResult:
    """Mock result from agent.run_sync()."""

    output: SemanticValidationResult


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager."""
    mock = Mock()
    # Mock the models_config attribute that ModelManager needs
    mock.models_config = []
    return mock


@pytest.fixture
def mock_instructions_manager():
    """Create a mock InstructionsManager."""
    return Mock()


@pytest.fixture
def mock_agent():
    """Create a mock agent that returns SemanticValidationResult."""
    agent = Mock()

    # Default successful validation result
    result = SemanticValidationResult(
        confidence_score=5,
        reasoning="Perfect alignment - correct metric type handling, exact filters, correct time window, and appropriate aggregation function.",
    )

    agent.run_sync.return_value = MockAgentResult(output=result)
    return agent


@pytest.fixture
def explainer_agent(
    mock_config_manager, mock_instructions_manager, mock_agent, monkeypatch
):
    """Create PromQLQueryExplainerAgent with mocked dependencies."""

    # Mock the _init_agent method to prevent actual agent initialization
    def mock_init_agent(self):
        self.agent = mock_agent

    # Patch _init_agent before creating the instance
    monkeypatch.setattr(PromQLQueryExplainerAgent, "_init_agent", mock_init_agent)

    # Create the agent instance (now with mocked initialization)
    agent = PromQLQueryExplainerAgent(mock_config_manager, mock_instructions_manager)

    return agent


class TestValidateSemanticMatch:
    """Test semantic validation functionality."""

    def test_validate_semantic_match_success(self, explainer_agent, mock_agent):
        """Test successful semantic validation with matching intent."""
        # Arrange
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            meter_type="counter",
            filters={"status": "500"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate")
            ],
        )
        query = 'rate(http_requests_total{status="500"}[5m])'

        # Act
        result = explainer_agent.validate_semantic_match(intent, query)

        # Assert
        assert isinstance(result, SemanticValidationResult)
        assert result.confidence_score == 5
        assert result.is_valid is True
        mock_agent.run_sync.assert_called_once()

    def test_validate_semantic_match_with_mismatch(self, explainer_agent, mock_agent):
        """Test semantic validation when query doesn't match intent."""
        # Arrange - mock a mismatch result
        mismatch_result = SemanticValidationResult(
            confidence_score=1,
            reasoning="Critical error - applying rate() to a gauge metric. Rate is for counters that always increase, not gauges with fluctuating values.",
        )
        mock_agent.run_sync.return_value = MockAgentResult(output=mismatch_result)

        intent = MetricsQueryIntent(
            metric="memory_usage_bytes",
            meter_type="gauge",
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="avg_over_time")
            ],
        )
        query = "rate(memory_usage_bytes[5m])"

        # Act
        result = explainer_agent.validate_semantic_match(intent, query)

        # Assert
        assert result.confidence_score == 1
        assert result.is_valid is False
        assert "gauge" in result.reasoning.lower()

    def test_validate_semantic_match_with_partial_match(
        self, explainer_agent, mock_agent
    ):
        """Test semantic validation when query has high confidence but isn't perfect."""
        # Arrange - mock a high confidence result
        partial_result = SemanticValidationResult(
            confidence_score=4,
            reasoning="Uses 99th percentile instead of 95th, but the query structure is correct and will provide useful latency data. The difference is minor and doesn't compromise the monitoring goal.",
        )
        mock_agent.run_sync.return_value = MockAgentResult(output=partial_result)

        intent = MetricsQueryIntent(
            metric="api_latency_seconds",
            meter_type="histogram",
            filters={"endpoint": "/users"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(
                    function_name="histogram_quantile", params={"quantile": 0.95}
                )
            ],
        )
        query = 'histogram_quantile(0.99, rate(api_latency_seconds_bucket{endpoint="/users"}[5m]))'

        # Act
        result = explainer_agent.validate_semantic_match(intent, query)

        # Assert
        assert result.confidence_score == 4
        assert result.is_valid is True  # Score 4 is above threshold 2
        assert "99th" in result.reasoning or "0.99" in result.reasoning

    def test_validate_semantic_match_llm_failure_raises_error(
        self, explainer_agent, mock_agent
    ):
        """Test that LLM failure is properly wrapped in SemanticValidationError."""
        # Arrange
        mock_agent.run_sync.side_effect = Exception("LLM API error")
        intent = MetricsQueryIntent(metric="test_metric", meter_type="counter")
        query = "test_query"

        # Act & Assert
        with pytest.raises(
            SemanticValidationError, match="Failed to validate query semantics"
        ):
            explainer_agent.validate_semantic_match(intent, query)


class TestFormatValidationPrompt:
    """Test prompt formatting functionality."""

    def test_format_validation_prompt_basic(self, explainer_agent):
        """Test basic prompt formatting."""
        intent = MetricsQueryIntent(
            metric="cpu_usage", meter_type="gauge", window="5m"
        )
        query = "avg_over_time(cpu_usage[5m])"

        prompt = explainer_agent._format_validation_prompt(intent, query)

        assert "cpu_usage" in prompt
        assert "gauge" in prompt
        assert "5m" in prompt
        assert query in prompt

    def test_format_validation_prompt_with_aggregations(self, explainer_agent):
        """Test prompt formatting with aggregation suggestions."""
        intent = MetricsQueryIntent(
            metric="http_requests",
            meter_type="counter",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate"),
                AggregationFunctionSuggestion(
                    function_name="histogram_quantile", params={"quantile": 0.95}
                ),
            ],
        )
        query = "rate(http_requests[5m])"

        prompt = explainer_agent._format_validation_prompt(intent, query)

        assert "rate" in prompt
        assert "histogram_quantile" in prompt
        assert "quantile=0.95" in prompt

    def test_format_validation_prompt_with_group_by(self, explainer_agent):
        """Test prompt formatting with group by dimensions."""
        intent = MetricsQueryIntent(metric="requests", meter_type="counter", group_by=["instance", "job"])
        query = "sum(requests) by (instance, job)"

        prompt = explainer_agent._format_validation_prompt(intent, query)

        assert "instance" in prompt
        assert "job" in prompt
