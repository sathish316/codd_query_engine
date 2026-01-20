"""
Unit tests for PromQLMetricNameExtractorAgent.

Tests cover:
- Successful metric extraction (single, multiple, dotted identifiers)
- Noise resilience (operators, numbers, function calls)
- Error handling (LLM exceptions, low confidence, invalid names)
- MetricExtractionResponse validation and normalization
- Parser without network calls using stub agent

All tests use mock/stub agents to avoid real OpenAI API calls.
"""

from unittest.mock import Mock, patch
import pytest

from codd_engine.validation_engine.agent.metrics.promql_metricname_extractor_agent import (
    PromQLMetricNameExtractorAgent,
    VALID_METRIC_NAME_PATTERN,
    MetricExtractionResponse,
    MetricExpressionParseError,
)


class StubAgentResult:
    """Stub for PydanticAI agent result."""

    def __init__(self, data: MetricExtractionResponse):
        self.output = data


class StubAgent:
    """
    Stub agent that returns deterministic responses for testing.

    This stub avoids real OpenAI API calls and allows testing
    the parser logic in isolation.
    """

    def __init__(
        self,
        metric_names: list[str] = None,
        confidence: float = 1.0,
        raise_error: Exception = None,
    ):
        self.metric_names = metric_names or []
        self.confidence = confidence
        self.raise_error = raise_error
        self.calls = []

    def run_sync(self, expression: str) -> StubAgentResult:
        """Simulate agent.run_sync() call."""
        self.calls.append(expression)
        if self.raise_error:
            raise self.raise_error
        response = MetricExtractionResponse(
            metric_names=self.metric_names, confidence=self.confidence
        )
        return StubAgentResult(response)


class TestPromQLMetricNameExtractorAgent:
    """Tests for PromQLMetricNameExtractorAgent."""

    @pytest.fixture
    def mock_config_manager(self):
        return Mock()

    @pytest.fixture
    def mock_instructions_manager(self):
        return Mock()

    @pytest.fixture
    def mock_agent_builder(self):
        with patch(
            "codd_engine.validation_engine.agent.metrics.promql_metricname_extractor_agent.AgentBuilder"
        ) as builder_cls:
            builder_instance = builder_cls.return_value
            # Chain mocks - each method returns the builder instance for chaining
            builder_instance.set_system_prompt_keys.return_value = builder_instance
            builder_instance.name.return_value = builder_instance
            builder_instance.add_instructions_manager.return_value = builder_instance
            builder_instance.add_model_manager.return_value = builder_instance
            builder_instance.instruction.return_value = builder_instance
            builder_instance.set_output_type.return_value = builder_instance

            yield builder_cls

    def _create_extractor(
        self, config_manager, instructions_manager, stub_agent, mock_agent_builder
    ):
        """Helper to create extractor with injected stub agent."""
        # Set up the mock to return stub agent when build_simple_agent is called
        builder_instance = mock_agent_builder.return_value
        builder_instance.build_simple_agent.return_value = stub_agent

        # Create the extractor - this will call _init_agent which uses the mocked builder
        return PromQLMetricNameExtractorAgent(config_manager, instructions_manager)

    def test_parse_single_metric(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test parsing expression with single metric."""
        agent = StubAgent(metric_names=["cpu.usage"])
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("cpu.usage")

        assert result == {"cpu.usage"}
        assert len(agent.calls) == 1

    def test_parse_multiple_metrics(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test parsing expression with multiple metrics."""
        agent = StubAgent(
            metric_names=["cpu.usage", "memory.total", "disk.io"],
        )
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("cpu.usage + memory.total + disk.io")

        assert result == {"cpu.usage", "memory.total", "disk.io"}

    def test_parse_dotted_identifiers(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test parsing dotted metric identifiers."""
        agent = StubAgent(
            metric_names=["system.cpu.user", "system.memory.available.bytes"],
        )
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("system.cpu.user / system.memory.available.bytes")

        assert "system.cpu.user" in result
        assert "system.memory.available.bytes" in result

    def test_parse_underscored_identifiers(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test parsing underscored metric identifiers."""
        agent = StubAgent(
            metric_names=["cpu_usage_percent", "memory_total_bytes"],
        )
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("cpu_usage_percent + memory_total_bytes")

        assert result == {"cpu_usage_percent", "memory_total_bytes"}

    def test_parse_empty_expression(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test parsing empty expression returns empty set."""
        agent = StubAgent()
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("")

        assert result == set()
        assert len(agent.calls) == 0  # Agent not called for empty

        result = parser.parse("   \t\n  ")

        assert result == set()
        assert len(agent.calls) == 0

        result = parser.parse(None)

        assert result == set()
        assert len(agent.calls) == 0

    def test_parse_expression_with_operators(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test that operators are ignored in extraction."""
        agent = StubAgent(
            metric_names=["cpu.usage", "memory.total"],
        )
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("(cpu.usage + memory.total) * 100 / 2")

        assert result == {"cpu.usage", "memory.total"}

    def test_parse_expression_with_numbers(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test that numbers are not included as metrics."""
        agent = StubAgent(metric_names=["cpu.idle"], confidence=1.0)
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("100 - cpu.idle")

        assert result == {"cpu.idle"}

    def test_parse_expression_with_function_calls(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test that function names are not included as metrics."""
        agent = StubAgent(metric_names=["http.requests.count"])
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("avg(http.requests.count)")

        assert result == {"http.requests.count"}

    def test_parse_deduplicates_results(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test that duplicate metrics are deduplicated."""
        agent = StubAgent(metric_names=["cpu.usage", "cpu.usage", "memory.total"])
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("cpu.usage + cpu.usage")

        assert result == {"cpu.usage", "memory.total"}

    def test_parse_normalizes_case(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test that metric names are normalized to lowercase."""
        agent = StubAgent(metric_names=["CPU.Usage", "Memory.TOTAL"])
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("CPU.Usage + Memory.TOTAL")

        assert result == {"cpu.usage", "memory.total"}

    def test_parse_filters_invalid_names(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test that invalid metric names are filtered out."""
        agent = StubAgent(
            metric_names=["cpu.usage", "123invalid", "-bad.name", "good.metric"]
        )
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("some expression")

        assert "cpu.usage" in result
        assert "good.metric" in result
        assert "123invalid" not in result
        assert "-bad.name" not in result

    def test_parse_agent_error_raises_parse_error(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test that agent errors are wrapped in MetricExpressionParseError."""
        agent = StubAgent(raise_error=RuntimeError("API Error"))
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        with pytest.raises(MetricExpressionParseError):
            parser.parse("cpu.usage")

    def test_parse_empty_result_from_agent(
        self, mock_config_manager, mock_instructions_manager, mock_agent_builder
    ):
        """Test parsing when agent returns no metrics."""
        agent = StubAgent(metric_names=[])
        parser = self._create_extractor(
            mock_config_manager, mock_instructions_manager, agent, mock_agent_builder
        )

        result = parser.parse("no metrics here")

        assert result == set()


class TestValidMetricNamePattern:
    """Tests for VALID_METRIC_NAME_PATTERN regex."""

    def test_valid_simple_name(self):
        """Test simple lowercase name is valid."""
        assert VALID_METRIC_NAME_PATTERN.match("cpu")

    def test_valid_dotted_name(self):
        """Test dotted name is valid."""
        assert VALID_METRIC_NAME_PATTERN.match("cpu.usage")

    def test_valid_underscored_name(self):
        """Test underscored name is valid."""
        assert VALID_METRIC_NAME_PATTERN.match("cpu_usage")

    def test_valid_mixed_name(self):
        """Test mixed name is valid."""
        assert VALID_METRIC_NAME_PATTERN.match("system.cpu_usage.percent1")

    def test_valid_with_numbers(self):
        """Test name with numbers is valid."""
        assert VALID_METRIC_NAME_PATTERN.match("cpu1.usage2")

    def test_invalid_starts_with_number(self):
        """Test name starting with number is invalid."""
        assert not VALID_METRIC_NAME_PATTERN.match("1cpu")

    def test_invalid_starts_with_underscore(self):
        """Test name starting with underscore is invalid."""
        assert not VALID_METRIC_NAME_PATTERN.match("_cpu")

    def test_invalid_starts_with_dot(self):
        """Test name starting with dot is invalid."""
        assert not VALID_METRIC_NAME_PATTERN.match(".cpu")

    def test_invalid_uppercase(self):
        """Test uppercase name is invalid."""
        assert not VALID_METRIC_NAME_PATTERN.match("CPU")

    def test_invalid_special_chars(self):
        """Test name with special chars is invalid."""
        assert not VALID_METRIC_NAME_PATTERN.match("cpu-usage")
        assert not VALID_METRIC_NAME_PATTERN.match("cpu@usage")

    def test_invalid_empty(self):
        """Test empty name is invalid."""
        assert not VALID_METRIC_NAME_PATTERN.match("")
