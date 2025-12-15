"""
Unit tests for PydanticAIMetricExpressionParser.

Tests cover:
- Successful metric extraction (single, multiple, dotted identifiers)
- Noise resilience (operators, numbers, function calls)
- Error handling (LLM exceptions, low confidence, invalid names)
- MetricExtractionResponse validation and normalization
- Parser without network calls using stub agent

All tests use mock/stub agents to avoid real OpenAI API calls.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass

# Add parent directory to path to allow imports from maverick-engine
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import importlib.util

# Import LLMSettings
spec_settings = importlib.util.spec_from_file_location(
    "llm_settings",
    project_root / "maverick-engine" / "config" / "llm_settings.py"
)
llm_settings = importlib.util.module_from_spec(spec_settings)
spec_settings.loader.exec_module(llm_settings)
LLMSettings = llm_settings.LLMSettings
load_llm_settings = llm_settings.load_llm_settings

# Import PydanticAIMetricExpressionParser and MetricExtractionResponse using a single module instance
# loaded from file while registering in sys.modules to keep exception classes identical.
spec_parser = importlib.util.spec_from_file_location(
    "pydantic_metric_parser",
    project_root / "maverick-engine" / "validation_engine" / "pydantic_metric_parser.py"
)
parser_module = importlib.util.module_from_spec(spec_parser)
sys.modules["pydantic_metric_parser"] = parser_module
spec_parser.loader.exec_module(parser_module)
PydanticAIMetricExpressionParser = parser_module.PydanticAIMetricExpressionParser
MetricExtractionResponse = parser_module.MetricExtractionResponse
VALID_METRIC_NAME_PATTERN = parser_module.VALID_METRIC_NAME_PATTERN
MetricExpressionParseError = parser_module.MetricExpressionParseError


class StubAgentResult:
    """Stub for PydanticAI agent result."""

    def __init__(self, data: MetricExtractionResponse):
        self.data = data


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
        raise_error: Exception = None
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
            metric_names=self.metric_names,
            confidence=self.confidence
        )
        return StubAgentResult(response)


@pytest.fixture
def default_settings():
    """Provide default LLM settings for testing."""
    return LLMSettings(
        api_key="test-api-key",
        model_name="gpt-4o-mini",
        temperature=0.0,
        max_tokens=256,
        timeout=30,
        max_retries=3,
        confidence_threshold=0.7
    )


class TestMetricExtractionResponse:
    """Tests for MetricExtractionResponse Pydantic model."""

    def test_normalize_metric_names_lowercase(self):
        """Test that metric names are normalized to lowercase."""
        response = MetricExtractionResponse(
            metric_names=["CPU.Usage", "MEMORY.TOTAL", "Disk.IO"],
            confidence=1.0
        )
        assert response.metric_names == ["cpu.usage", "memory.total", "disk.io"]

    def test_normalize_metric_names_strip_whitespace(self):
        """Test that whitespace is stripped from metric names."""
        response = MetricExtractionResponse(
            metric_names=["  cpu.usage  ", "\tmemory.total\n", " disk.io"],
            confidence=1.0
        )
        assert response.metric_names == ["cpu.usage", "memory.total", "disk.io"]

    def test_normalize_metric_names_remove_empty(self):
        """Test that empty strings are removed from metric names."""
        response = MetricExtractionResponse(
            metric_names=["cpu.usage", "", "  ", "memory.total", None],
            confidence=1.0
        )
        # Note: None gets filtered out in normalize_metric_names
        assert "cpu.usage" in response.metric_names
        assert "memory.total" in response.metric_names
        assert "" not in response.metric_names

    def test_dedupe_metric_names(self):
        """Test that duplicate metric names are removed."""
        response = MetricExtractionResponse(
            metric_names=["cpu.usage", "memory.total", "cpu.usage", "memory.total"],
            confidence=1.0
        )
        assert response.metric_names == ["cpu.usage", "memory.total"]

    def test_dedupe_preserves_order(self):
        """Test that deduplication preserves first occurrence order."""
        response = MetricExtractionResponse(
            metric_names=["zebra", "alpha", "zebra", "beta", "alpha"],
            confidence=1.0
        )
        assert response.metric_names == ["zebra", "alpha", "beta"]

    def test_confidence_clamped_to_valid_range(self):
        """Test that confidence is clamped to [0.0, 1.0]."""
        response_high = MetricExtractionResponse(
            metric_names=["cpu"],
            confidence=1.5
        )
        assert response_high.confidence == 1.0

        response_low = MetricExtractionResponse(
            metric_names=["cpu"],
            confidence=-0.5
        )
        assert response_low.confidence == 0.0

    def test_confidence_invalid_type_defaults_to_zero(self):
        """Test that invalid confidence type defaults to 0.0."""
        response = MetricExtractionResponse(
            metric_names=["cpu"],
            confidence="not a number"
        )
        assert response.confidence == 0.0

    def test_metric_names_non_list_returns_empty(self):
        """Test that non-list metric_names returns empty list."""
        response = MetricExtractionResponse(
            metric_names="not a list",
            confidence=1.0
        )
        assert response.metric_names == []


class TestLLMSettings:
    """Tests for LLMSettings configuration."""

    def test_default_values(self):
        """Test default settings values."""
        settings = LLMSettings()
        assert settings.model_name == "gpt-4o-mini"
        assert settings.temperature == 0.0
        assert settings.max_tokens == 256
        assert settings.timeout == 30
        assert settings.max_retries == 3
        assert settings.confidence_threshold == 0.7

    def test_has_api_key_true(self):
        """Test has_api_key returns True when key is set."""
        settings = LLMSettings(api_key="valid-key")
        assert settings.has_api_key is True

    def test_has_api_key_false_none(self):
        """Test has_api_key returns False when key is None."""
        settings = LLMSettings(api_key=None)
        assert settings.has_api_key is False

    def test_has_api_key_false_empty(self):
        """Test has_api_key returns False when key is empty."""
        settings = LLMSettings(api_key="")
        assert settings.has_api_key is False

    def test_has_api_key_false_whitespace(self):
        """Test has_api_key returns False when key is whitespace."""
        settings = LLMSettings(api_key="   ")
        assert settings.has_api_key is False

    def test_invalid_temperature_raises(self):
        """Test that invalid temperature raises ValueError."""
        with pytest.raises(ValueError, match="Temperature"):
            LLMSettings(temperature=2.5)

    def test_invalid_max_tokens_raises(self):
        """Test that invalid max_tokens raises ValueError."""
        with pytest.raises(ValueError, match="max_tokens"):
            LLMSettings(max_tokens=0)

    def test_invalid_timeout_raises(self):
        """Test that invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout"):
            LLMSettings(timeout=0)

    def test_invalid_confidence_threshold_raises(self):
        """Test that invalid confidence_threshold raises ValueError."""
        with pytest.raises(ValueError, match="confidence_threshold"):
            LLMSettings(confidence_threshold=1.5)


class TestPydanticAIMetricExpressionParser:
    """Tests for PydanticAIMetricExpressionParser."""

    def test_parse_single_metric(self, default_settings):
        """Test parsing expression with single metric."""
        agent = StubAgent(metric_names=["cpu.usage"], confidence=1.0)
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("cpu.usage")

        assert result == {"cpu.usage"}
        assert len(agent.calls) == 1

    def test_parse_multiple_metrics(self, default_settings):
        """Test parsing expression with multiple metrics."""
        agent = StubAgent(
            metric_names=["cpu.usage", "memory.total", "disk.io"],
            confidence=0.95
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("cpu.usage + memory.total + disk.io")

        assert result == {"cpu.usage", "memory.total", "disk.io"}

    def test_parse_dotted_identifiers(self, default_settings):
        """Test parsing dotted metric identifiers."""
        agent = StubAgent(
            metric_names=["system.cpu.user", "system.memory.available.bytes"],
            confidence=1.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("system.cpu.user / system.memory.available.bytes")

        assert "system.cpu.user" in result
        assert "system.memory.available.bytes" in result

    def test_parse_underscored_identifiers(self, default_settings):
        """Test parsing underscored metric identifiers."""
        agent = StubAgent(
            metric_names=["cpu_usage_percent", "memory_total_bytes"],
            confidence=1.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("cpu_usage_percent + memory_total_bytes")

        assert result == {"cpu_usage_percent", "memory_total_bytes"}

    def test_parse_empty_expression(self, default_settings):
        """Test parsing empty expression returns empty set."""
        agent = StubAgent()
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("")

        assert result == set()
        assert len(agent.calls) == 0  # Agent not called for empty

    def test_parse_whitespace_expression(self, default_settings):
        """Test parsing whitespace-only expression returns empty set."""
        agent = StubAgent()
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("   \t\n  ")

        assert result == set()
        assert len(agent.calls) == 0

    def test_parse_none_expression(self, default_settings):
        """Test parsing None expression returns empty set."""
        agent = StubAgent()
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse(None)

        assert result == set()

    def test_parse_expression_with_operators(self, default_settings):
        """Test that operators are ignored in extraction."""
        agent = StubAgent(
            metric_names=["cpu.usage", "memory.total"],
            confidence=1.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("(cpu.usage + memory.total) * 100 / 2")

        assert result == {"cpu.usage", "memory.total"}

    def test_parse_expression_with_numbers(self, default_settings):
        """Test that numbers are not included as metrics."""
        agent = StubAgent(
            metric_names=["cpu.idle"],
            confidence=1.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("100 - cpu.idle")

        assert result == {"cpu.idle"}

    def test_parse_expression_with_function_calls(self, default_settings):
        """Test that function names are not included as metrics."""
        agent = StubAgent(
            metric_names=["http.requests.count"],
            confidence=1.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("avg(http.requests.count)")

        assert result == {"http.requests.count"}

    def test_parse_deduplicates_results(self, default_settings):
        """Test that duplicate metrics are deduplicated."""
        agent = StubAgent(
            metric_names=["cpu.usage", "cpu.usage", "memory.total"],
            confidence=1.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("cpu.usage + cpu.usage")

        assert result == {"cpu.usage", "memory.total"}

    def test_parse_normalizes_case(self, default_settings):
        """Test that metric names are normalized to lowercase."""
        agent = StubAgent(
            metric_names=["CPU.Usage", "Memory.TOTAL"],
            confidence=1.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("CPU.Usage + Memory.TOTAL")

        assert result == {"cpu.usage", "memory.total"}

    def test_parse_filters_invalid_names(self, default_settings):
        """Test that invalid metric names are filtered out."""
        agent = StubAgent(
            metric_names=["cpu.usage", "123invalid", "-bad.name", "good.metric"],
            confidence=1.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("some expression")

        assert "cpu.usage" in result
        assert "good.metric" in result
        assert "123invalid" not in result
        assert "-bad.name" not in result

    def test_parse_agent_error_raises_parse_error(self, default_settings):
        """Test that agent errors are wrapped in MetricExpressionParseError."""
        agent = StubAgent(raise_error=RuntimeError("API Error"))
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        with pytest.raises(MetricExpressionParseError):
            parser.parse("cpu.usage")

    def test_parse_no_api_key_raises_parse_error(self):
        """Test that missing API key raises MetricExpressionParseError."""
        settings = LLMSettings(api_key=None)
        parser = PydanticAIMetricExpressionParser(settings)

        with pytest.raises(MetricExpressionParseError, match="OPENAI_API_KEY"):
            parser.parse("cpu.usage")

    def test_parse_low_confidence_still_returns_results(self, default_settings):
        """Test that low confidence results are still returned (with warning)."""
        settings = LLMSettings(
            api_key="test-key",
            confidence_threshold=0.8
        )
        agent = StubAgent(
            metric_names=["cpu.usage"],
            confidence=0.5  # Below threshold
        )
        parser = PydanticAIMetricExpressionParser(settings, agent=agent)

        # Should still return results, just log warning
        result = parser.parse("ambiguous expression")

        assert result == {"cpu.usage"}

    def test_parse_zero_confidence(self, default_settings):
        """Test parsing with zero confidence."""
        agent = StubAgent(
            metric_names=["cpu.usage"],
            confidence=0.0
        )
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        result = parser.parse("expression")

        assert result == {"cpu.usage"}

    def test_parse_empty_result_from_agent(self, default_settings):
        """Test parsing when agent returns no metrics."""
        agent = StubAgent(metric_names=[], confidence=1.0)
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

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


class TestErrorClassification:
    """Tests for error classification in parser."""

    def test_classify_auth_error(self, default_settings):
        """Test authentication error classification."""
        agent = StubAgent(raise_error=RuntimeError("401 Unauthorized - Invalid API key"))
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        with pytest.raises(MetricExpressionParseError) as exc_info:
            parser.parse("cpu.usage")

        assert "authentication" in str(exc_info.value).lower()

    def test_classify_rate_limit_error(self, default_settings):
        """Test rate limit error classification."""
        agent = StubAgent(raise_error=RuntimeError("429 Rate limit exceeded"))
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        with pytest.raises(MetricExpressionParseError) as exc_info:
            parser.parse("cpu.usage")

        assert "rate limit" in str(exc_info.value).lower()

    def test_classify_timeout_error(self, default_settings):
        """Test timeout error classification."""
        agent = StubAgent(raise_error=TimeoutError("Request timed out"))
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        with pytest.raises(MetricExpressionParseError) as exc_info:
            parser.parse("cpu.usage")

        assert "timeout" in str(exc_info.value).lower()

    def test_classify_connection_error(self, default_settings):
        """Test connection error classification."""
        agent = StubAgent(raise_error=ConnectionError("Failed to connect"))
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        with pytest.raises(MetricExpressionParseError) as exc_info:
            parser.parse("cpu.usage")

        assert "connect" in str(exc_info.value).lower()

    def test_classify_generic_error(self, default_settings):
        """Test generic error classification."""
        agent = StubAgent(raise_error=RuntimeError("Something went wrong"))
        parser = PydanticAIMetricExpressionParser(default_settings, agent=agent)

        with pytest.raises(MetricExpressionParseError) as exc_info:
            parser.parse("cpu.usage")

        assert "extraction error" in str(exc_info.value).lower()


class TestLoadLLMSettings:
    """Tests for load_llm_settings function."""

    def test_load_from_environment(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        monkeypatch.setenv("OPENAI_MODEL_NAME", "gpt-4")
        monkeypatch.setenv("OPENAI_TEMPERATURE", "0.5")
        monkeypatch.setenv("OPENAI_MAX_TOKENS", "512")
        monkeypatch.setenv("OPENAI_TIMEOUT", "60")
        monkeypatch.setenv("LLM_MAX_RETRIES", "5")
        monkeypatch.setenv("LLM_CONFIDENCE_THRESHOLD", "0.9")

        settings = load_llm_settings()

        assert settings.api_key == "test-key-123"
        assert settings.model_name == "gpt-4"
        assert settings.temperature == 0.5
        assert settings.max_tokens == 512
        assert settings.timeout == 60
        assert settings.max_retries == 5
        assert settings.confidence_threshold == 0.9

    def test_load_defaults_when_env_missing(self, monkeypatch):
        """Test that defaults are used when env vars are missing."""
        # Clear any existing env vars
        for key in ["OPENAI_API_KEY", "OPENAI_MODEL_NAME", "OPENAI_TEMPERATURE",
                    "OPENAI_MAX_TOKENS", "OPENAI_TIMEOUT", "LLM_MAX_RETRIES",
                    "LLM_CONFIDENCE_THRESHOLD"]:
            monkeypatch.delenv(key, raising=False)

        settings = load_llm_settings()

        assert settings.api_key is None
        assert settings.model_name == "gpt-4o-mini"
        assert settings.temperature == 0.0
        assert settings.max_tokens == 256

    def test_load_invalid_numeric_uses_default(self, monkeypatch):
        """Test that invalid numeric values use defaults."""
        monkeypatch.setenv("OPENAI_TEMPERATURE", "not_a_number")
        monkeypatch.setenv("OPENAI_MAX_TOKENS", "invalid")

        settings = load_llm_settings()

        assert settings.temperature == 0.0
        assert settings.max_tokens == 256
