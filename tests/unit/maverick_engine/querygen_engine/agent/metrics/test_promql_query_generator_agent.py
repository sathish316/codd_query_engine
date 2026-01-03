"""
Unit tests for PromQL query generator agent with ReAct pattern.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from dataclasses import dataclass

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    PromQLQueryResponse,
)
from maverick_engine.querygen_engine.agent.metrics.promql_query_generator_agent import (
    PromQLQueryGeneratorAgent,
)
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    QueryGenerationResult,
)


@dataclass
class MockAgentResult:
    """Mock result from agent.run_sync()."""

    output: PromQLQueryResponse


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager."""
    mock = Mock()
    mock.models_config = []
    return mock


@pytest.fixture
def mock_instructions_manager():
    """Create a mock InstructionsManager."""
    return Mock()


@pytest.fixture
def mock_preprocessor():
    """Create a mock preprocessor that returns intent unchanged."""
    mock = Mock()
    mock.preprocess = lambda intent: intent
    return mock


@pytest.fixture
def mock_promql_validator():
    """Create a mock PromQL validator."""
    mock = Mock()
    return mock


@pytest.fixture
def generator_agent(
    mock_config_manager,
    mock_instructions_manager,
    mock_preprocessor,
    mock_promql_validator,
    monkeypatch,
):
    """Create PromQLQueryGeneratorAgent with mocked dependencies."""

    # Mock the _init_agent method to prevent actual agent initialization
    def mock_init_agent(self):
        self.agent = Mock()
        result = PromQLQueryResponse(
            query='rate(http_requests_total{status="500"}[5m])',
            reasoning="Generated rate() query for counter metric",
        )
        self.agent.run = AsyncMock(return_value=MockAgentResult(output=result))

    # Patch _init_agent before creating the instance
    monkeypatch.setattr(PromQLQueryGeneratorAgent, "_init_agent", mock_init_agent)

    # Create the agent instance (now with mocked initialization)
    agent = PromQLQueryGeneratorAgent(
        config_manager=mock_config_manager,
        instructions_manager=mock_instructions_manager,
        preprocessor=mock_preprocessor,
        promql_validator=mock_promql_validator,
    )

    return agent


class TestGenerateQuery:
    """Test query generation with ReAct pattern."""

    @pytest.mark.asyncio
    async def test_generate_query_for_counter_metric(self, generator_agent):
        """Test query generation for a counter metric with rate aggregation."""
        # Arrange
        intent = MetricsQueryIntent(
            metric="http_requests_total",
            intent_description="Calculate HTTP 5xx requests rate over the last 5 minutes",
            metric_type="counter",
            filters={"status": "500"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate")
            ],
        )

        # Act
        result = await generator_agent.generate_query("default", intent)

        # Assert
        assert isinstance(result, QueryGenerationResult)
        assert result.success is True
        assert "rate(" in result.query
        assert "http_requests_total" in result.query
