"""
Unit tests for PromQL query explainer agent.
"""

import pytest
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.validation_engine.metrics.structured_outputs import SemanticValidationResult
from maverick_engine.validation_engine.agent.metrics.promql_query_explainer_agent import (
    PromQLQueryExplainerAgent,
    SemanticValidationError,
)


@dataclass
class MockAgentResult:
    """Mock result from agent.run_sync()."""
    output: SemanticValidationResult


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager."""
    return Mock()


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
        intent_match=True,
        partial_match=False,
        explanation="Query correctly uses rate() on a counter metric",
        original_intent_summary="Calculate per-second rate of HTTP 500 errors over 5m",
        actual_query_behavior="Calculates per-second rate of http_requests_total with status=500 over 5 minutes",
        confidence=0.95
    )

    agent.run_sync.return_value = MockAgentResult(output=result)
    return agent


@pytest.fixture
def explainer_agent(mock_config_manager, mock_instructions_manager, mock_agent, monkeypatch):
    """Create PromQLQueryExplainerAgent with mocked dependencies."""
    # Create the agent instance
    agent = PromQLQueryExplainerAgent(mock_config_manager, mock_instructions_manager)

    # Replace the internal agent with our mock
    monkeypatch.setattr(agent, "agent", mock_agent)

    return agent


class TestPromQLQueryExplainerAgentInit:
    """Test agent initialization."""

    def test_init_creates_agent(self, mock_config_manager, mock_instructions_manager):
        """Test that initialization creates the underlying agent."""
        agent = PromQLQueryExplainerAgent(mock_config_manager, mock_instructions_manager)
        assert agent.config_manager == mock_config_manager
        assert agent.instructions_manager == mock_instructions_manager
        assert hasattr(agent, "agent")


class TestValidateSemanticMatch:
    """Test semantic validation functionality."""

    def test_validate_semantic_match_success(self, explainer_agent, mock_agent):
        """Test successful semantic validation with matching intent."""
        # Arrange
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            metric_type="counter",
            filters={"status": "500"},
            window="5m",
            aggregation_suggestions=[AggregationFunctionSuggestion(function_name="rate")]
        )
        query = 'rate(http_requests_total{status="500"}[5m])'

        # Act
        result = explainer_agent.validate_semantic_match(intent, query)

        # Assert
        assert isinstance(result, SemanticValidationResult)
        assert result.intent_match is True
        assert result.partial_match is False
        assert result.confidence == 0.95
        assert "rate()" in result.explanation
        mock_agent.run_sync.assert_called_once()

    def test_validate_semantic_match_with_mismatch(self, explainer_agent, mock_agent):
        """Test semantic validation when query doesn't match intent."""
        # Arrange - mock a mismatch result
        mismatch_result = SemanticValidationResult(
            intent_match=False,
            partial_match=False,
            explanation="Query uses rate() on a gauge metric, which is incorrect",
            original_intent_summary="Calculate average memory usage over 5m",
            actual_query_behavior="Calculates rate of change for memory_usage_bytes gauge",
            confidence=0.90
        )
        mock_agent.run_sync.return_value = MockAgentResult(output=mismatch_result)

        intent = MetricsQueryIntent(
            metric="memory_usage_bytes",
            metric_type="gauge",
            window="5m",
            aggregation_suggestions=[AggregationFunctionSuggestion(function_name="avg_over_time")]
        )
        query = "rate(memory_usage_bytes[5m])"

        # Act
        result = explainer_agent.validate_semantic_match(intent, query)

        # Assert
        assert result.intent_match is False
        assert result.partial_match is False
        assert result.confidence == 0.90
        assert "gauge" in result.explanation.lower()

    def test_validate_semantic_match_with_partial_match(self, explainer_agent, mock_agent):
        """Test semantic validation when query partially matches intent."""
        # Arrange - mock a partial match result
        partial_result = SemanticValidationResult(
            intent_match=False,
            partial_match=True,
            explanation="Query uses 99th percentile instead of 95th, but structure is correct",
            original_intent_summary="Calculate 95th percentile latency for /users endpoint",
            actual_query_behavior="Calculates 99th percentile latency for /users endpoint",
            confidence=0.85
        )
        mock_agent.run_sync.return_value = MockAgentResult(output=partial_result)

        intent = MetricsQueryIntent(
            metric="api_latency_seconds",
            metric_type="histogram",
            filters={"endpoint": "/users"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(
                    function_name="histogram_quantile",
                    params={"quantile": 0.95}
                )
            ]
        )
        query = 'histogram_quantile(0.99, rate(api_latency_seconds_bucket{endpoint="/users"}[5m]))'

        # Act
        result = explainer_agent.validate_semantic_match(intent, query)

        # Assert
        assert result.intent_match is False
        assert result.partial_match is True
        assert result.confidence == 0.85
        assert "99th" in result.explanation or "0.99" in result.explanation

    def test_validate_semantic_match_with_filters(self, explainer_agent, mock_agent):
        """Test validation with multiple filters."""
        # Arrange
        intent = MetricsQueryIntent(
            metric="api_latency_seconds",
            metric_type="histogram",
            filters={"endpoint": "/users", "method": "GET"},
            window="5m",
            group_by=["instance"],
            aggregation_suggestions=[
                AggregationFunctionSuggestion(
                    function_name="histogram_quantile",
                    params={"quantile": 0.95}
                )
            ]
        )
        query = 'histogram_quantile(0.95, rate(api_latency_seconds_bucket{endpoint="/users",method="GET"}[5m])) by (instance)'

        # Act
        result = explainer_agent.validate_semantic_match(intent, query)

        # Assert
        assert isinstance(result, SemanticValidationResult)
        mock_agent.run_sync.assert_called_once()

        # Verify the prompt contains filter information
        call_args = mock_agent.run_sync.call_args[0][0]
        assert "endpoint=/users" in call_args
        assert "method=GET" in call_args

    def test_validate_semantic_match_empty_query_raises_error(self, explainer_agent):
        """Test that empty query raises SemanticValidationError."""
        intent = MetricsQueryIntent(metric="test_metric")

        with pytest.raises(SemanticValidationError, match="cannot be empty"):
            explainer_agent.validate_semantic_match(intent, "")

    def test_validate_semantic_match_no_metric_raises_error(self, explainer_agent):
        """Test that intent without metric raises SemanticValidationError."""
        intent = MetricsQueryIntent(metric="")

        with pytest.raises(SemanticValidationError, match="must specify a metric"):
            explainer_agent.validate_semantic_match(intent, "rate(some_metric[5m])")

    def test_validate_semantic_match_llm_failure_raises_error(self, explainer_agent, mock_agent):
        """Test that LLM failure is properly wrapped in SemanticValidationError."""
        # Arrange
        mock_agent.run_sync.side_effect = Exception("LLM API error")
        intent = MetricsQueryIntent(metric="test_metric")
        query = "test_query"

        # Act & Assert
        with pytest.raises(SemanticValidationError, match="Failed to validate query semantics"):
            explainer_agent.validate_semantic_match(intent, query)


class TestFormatValidationPrompt:
    """Test prompt formatting functionality."""

    def test_format_validation_prompt_basic(self, explainer_agent):
        """Test basic prompt formatting."""
        intent = MetricsQueryIntent(
            metric="cpu_usage",
            metric_type="gauge",
            window="5m"
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
            metric_type="counter",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate"),
                AggregationFunctionSuggestion(
                    function_name="histogram_quantile",
                    params={"quantile": 0.95}
                )
            ]
        )
        query = "rate(http_requests[5m])"

        prompt = explainer_agent._format_validation_prompt(intent, query)

        assert "rate" in prompt
        assert "histogram_quantile" in prompt
        assert "quantile=0.95" in prompt

    def test_format_validation_prompt_with_group_by(self, explainer_agent):
        """Test prompt formatting with group by dimensions."""
        intent = MetricsQueryIntent(
            metric="requests",
            group_by=["instance", "job"]
        )
        query = "sum(requests) by (instance, job)"

        prompt = explainer_agent._format_validation_prompt(intent, query)

        assert "instance" in prompt
        assert "job" in prompt


class TestExplainQuery:
    """Test query explanation functionality."""

    def test_explain_query_success(self, explainer_agent, mock_agent):
        """Test successful query explanation."""
        # Arrange
        explanation_result = SemanticValidationResult(
            intent_match=True,
            partial_match=False,
            explanation="Not applicable for standalone explanation",
            original_intent_summary="Not applicable",
            actual_query_behavior="Calculates the per-second rate of HTTP requests over 5 minutes",
            confidence=0.95
        )
        mock_agent.run_sync.return_value = MockAgentResult(output=explanation_result)

        query = 'rate(http_requests_total[5m])'

        # Act
        explanation = explainer_agent.explain_query(query)

        # Assert
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        mock_agent.run_sync.assert_called_once()

    def test_explain_query_empty_raises_error(self, explainer_agent):
        """Test that empty query raises SemanticValidationError."""
        with pytest.raises(SemanticValidationError, match="cannot be empty"):
            explainer_agent.explain_query("")

    def test_explain_query_llm_failure_raises_error(self, explainer_agent, mock_agent):
        """Test that LLM failure is properly wrapped in SemanticValidationError."""
        mock_agent.run_sync.side_effect = Exception("API error")

        with pytest.raises(SemanticValidationError, match="Failed to explain query"):
            explainer_agent.explain_query("rate(metric[5m])")


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_validate_with_no_aggregation_suggestions(self, explainer_agent):
        """Test validation when no aggregation suggestions are provided."""
        intent = MetricsQueryIntent(
            metric="simple_metric",
            metric_type="gauge"
        )
        query = "simple_metric"

        prompt = explainer_agent._format_validation_prompt(intent, query)
        assert "None" in prompt  # Should show "None" for aggregations

    def test_validate_with_empty_filters(self, explainer_agent):
        """Test validation when filters dict is empty."""
        intent = MetricsQueryIntent(
            metric="test_metric",
            filters={}
        )
        query = "test_metric"

        prompt = explainer_agent._format_validation_prompt(intent, query)
        # Should not crash and should handle empty filters gracefully
        assert "test_metric" in prompt

    def test_validate_with_complex_aggregation_params(self, explainer_agent):
        """Test validation with complex aggregation parameters."""
        intent = MetricsQueryIntent(
            metric="latency",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(
                    function_name="histogram_quantile",
                    params={
                        "quantile": 0.95,
                        "le": "+Inf",
                        "buckets": [0.1, 0.5, 1.0, 5.0]
                    }
                )
            ]
        )
        query = "histogram_quantile(0.95, latency)"

        prompt = explainer_agent._format_validation_prompt(intent, query)
        assert "histogram_quantile" in prompt
        assert "0.95" in prompt
