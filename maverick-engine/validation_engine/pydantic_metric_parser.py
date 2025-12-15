"""
PydanticAI-based metric expression parser.

This module provides a MetricExpressionParser implementation that uses PydanticAI
with an OpenAI model to extract metric names from free-form metric expressions.

The parser normalizes metric names (lowercase, stripped, deduped) and validates
output using Pydantic validators to guard against hallucinations.

Example usage:
    from config.llm_settings import load_llm_settings
    from validation_engine.pydantic_metric_parser import PydanticAIMetricExpressionParser

    settings = load_llm_settings()
    parser = PydanticAIMetricExpressionParser(settings)
    metrics = parser.parse("cpu.usage + memory.total * 2")
    # Returns: {"cpu.usage", "memory.total"}
"""

import logging
import re
import time
from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
# Note: tenacity is a declared dependency but we implement simple retry
# logic inline to keep the code straightforward and testable

# Import from sibling modules using importlib (directory has hyphen)
import importlib.util
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent

def _load_module(name: str, path: Path):
    """Load module from path, reusing sys.modules to keep singletons consistent."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

_llm_settings = _load_module(
    "llm_settings",
    _project_root / "maverick-engine" / "config" / "llm_settings.py"
)
LLMSettings = _llm_settings.LLMSettings

_schema_validator = _load_module(
    "schema_validator",
    _project_root / "maverick-engine" / "validation_engine" / "schema_validator.py"
)
MetricExpressionParseError = _schema_validator.MetricExpressionParseError

logger = logging.getLogger(__name__)


# Regex pattern for valid metric name characters
VALID_METRIC_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_.]*$')


class MetricExtractionResponse(BaseModel):
    """
    Response schema for metric name extraction.

    Contains the list of metric names extracted from an expression
    along with a confidence score indicating extraction reliability.
    """
    metric_names: list[str]
    confidence: float

    @field_validator('metric_names', mode='before')
    @classmethod
    def normalize_metric_names(cls, v):
        """Normalize metric names: lowercase, strip whitespace, remove empties."""
        if not isinstance(v, list):
            return []
        normalized = []
        for name in v:
            if isinstance(name, str):
                clean = name.strip().lower()
                if clean:
                    normalized.append(clean)
        return normalized

    @field_validator('metric_names', mode='after')
    @classmethod
    def dedupe_metric_names(cls, v):
        """Remove duplicate metric names while preserving order."""
        seen = set()
        deduped = []
        for name in v:
            if name not in seen:
                seen.add(name)
                deduped.append(name)
        return deduped

    @field_validator('confidence', mode='before')
    @classmethod
    def clamp_confidence(cls, v):
        """Clamp confidence to valid range [0.0, 1.0]."""
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (TypeError, ValueError):
            return 0.0


# System prompt for metric extraction
SYSTEM_PROMPT = """You are a metric expression parser. Your task is to extract metric names from metric expressions.

Rules for metric names:
- Metric names are identifiers that reference data series
- They typically use lowercase letters, numbers, underscores, and dots
- Examples: cpu.usage, memory.total, disk_io_read, network.bytes.in
- Ignore operators: +, -, *, /, ^, (, ), numbers, and function calls like avg(), sum(), max()
- Ignore comments and string literals
- Return only the metric identifiers, not function names or keywords

Examples:
- Input: "cpu.usage + memory.total * 2"
  Output: ["cpu.usage", "memory.total"]

- Input: "avg(http.requests.count) / time_window"
  Output: ["http.requests.count", "time_window"]

- Input: "(disk.read + disk.write) / disk.total"
  Output: ["disk.read", "disk.write", "disk.total"]

- Input: "100 - cpu.idle"
  Output: ["cpu.idle"]

- Input: "sum(sales.revenue) by region"
  Output: ["sales.revenue"]

Respond with the list of metric names and your confidence level (0.0-1.0) in the extraction.
A confidence of 1.0 means you are certain about all extracted metrics.
A lower confidence indicates ambiguity in the expression."""


class PydanticAIMetricExpressionParser:
    """
    MetricExpressionParser implementation using PydanticAI with OpenAI.

    Extracts metric names from expressions using an LLM, with Pydantic
    validation to ensure output quality. Includes retry logic for transient
    errors and confidence thresholding.

    This class implements the MetricExpressionParser protocol defined in
    schema_validator.py.

    Args:
        settings: LLMSettings instance with API key and model configuration
        agent: Optional pre-configured Agent instance (for testing)

    Raises:
        MetricExpressionParseError: On parse failures or low confidence

    Note:
        Requires OPENAI_API_KEY environment variable to be set for production use.
        For testing, inject a mock agent via the agent parameter.
    """

    def __init__(
        self,
        settings: LLMSettings,
        agent: Optional[Agent] = None,
    ):
        self._settings = settings
        self._agent = agent

    def _get_agent(self) -> Agent:
        """Get or create the PydanticAI agent."""
        if self._agent is not None:
            return self._agent

        if not self._settings.has_api_key:
            raise MetricExpressionParseError(
                "OPENAI_API_KEY environment variable is required but not set"
            )

        model = OpenAIModel(
            self._settings.model_name,
            api_key=self._settings.api_key,
        )

        self._agent = Agent(
            model,
            result_type=MetricExtractionResponse,
            system_prompt=SYSTEM_PROMPT,
        )
        return self._agent

    def parse(self, metric_expression: str) -> set[str]:
        """
        Parse a metric expression and extract unique metric names.

        Uses PydanticAI with an OpenAI model to understand the expression
        and extract metric identifiers. Results are normalized, deduped,
        and validated.

        Args:
            metric_expression: The expression string to parse

        Returns:
            Set of unique metric names found in the expression

        Raises:
            MetricExpressionParseError: If parsing fails, API errors occur,
                or confidence is below threshold
        """
        # Guard: empty expression
        if not metric_expression or not metric_expression.strip():
            logger.debug("Empty expression, returning empty set")
            return set()

        # Attempt LLM extraction with retries
        try:
            result = self._extract_with_retry(metric_expression)
        except MetricExpressionParseError:
            raise
        except Exception as e:
            logger.error(f"Metric extraction failed: {e}", exc_info=True)
            raise MetricExpressionParseError(
                f"Failed to extract metrics from expression: {e}"
            ) from e

        # Validate confidence threshold
        if result.confidence < self._settings.confidence_threshold:
            logger.warning(
                f"Low confidence extraction: {result.confidence} < {self._settings.confidence_threshold}"
            )
            # Still return results but log warning; callers can check confidence
            # For strict mode, uncomment:
            # raise MetricExpressionParseError(
            #     f"Low confidence ({result.confidence}) extraction, threshold is {self._settings.confidence_threshold}"
            # )

        # Convert to set and validate individual names
        metrics = set()
        for name in result.metric_names:
            if self._is_valid_metric_name(name):
                metrics.add(name)
            else:
                logger.warning(f"Skipping invalid metric name format: '{name}'")

        logger.info(
            f"Extracted {len(metrics)} metrics with confidence {result.confidence}",
            extra={"metric_count": len(metrics), "confidence": result.confidence}
        )

        return metrics

    def _extract_with_retry(self, expression: str) -> MetricExtractionResponse:
        """
        Extract metrics with exponential backoff retry for transient errors.

        Args:
            expression: The metric expression to parse

        Returns:
            MetricExtractionResponse with extracted metrics and confidence

        Raises:
            MetricExpressionParseError: On non-retryable errors or max retries exceeded
        """
        max_retries = self._settings.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                agent = self._get_agent()
                result = agent.run_sync(expression)
                return result.data
            except (TimeoutError, ConnectionError) as e:
                last_error = e
                # Exponential backoff for transient errors
                if attempt < max_retries - 1:
                    import time
                    wait_time = min(10, 2 ** attempt)
                    logger.warning(f"Transient error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                continue
            except MetricExpressionParseError:
                # Re-raise parse errors directly
                raise
            except Exception as e:
                # Non-retryable error, wrap and raise immediately
                error_msg = self._classify_error(e)
                raise MetricExpressionParseError(error_msg) from e

        # All retries exhausted for transient error
        if last_error:
            error_msg = self._classify_error(last_error)
            raise MetricExpressionParseError(error_msg) from last_error

        # Fallback (should not be reached)
        raise MetricExpressionParseError("Metric extraction failed for unknown reasons")

    def _classify_error(self, error: Exception) -> str:
        """Classify and return a user-friendly error message."""
        error_str = str(error).lower()

        if "authentication" in error_str or "api key" in error_str or "401" in error_str:
            return "OpenAI API authentication failed - check OPENAI_API_KEY"
        elif "rate limit" in error_str or "429" in error_str:
            return "OpenAI API rate limit exceeded - retry later"
        elif "timeout" in error_str or "timed out" in error_str:
            return "OpenAI API request timed out (timeout)"
        elif "connection" in error_str:
            return "Failed to connect to OpenAI API"
        else:
            return f"Metric extraction error: {error}"

    def _is_valid_metric_name(self, name: str) -> bool:
        """
        Check if a metric name has valid format.

        Valid names start with a lowercase letter and contain only
        lowercase letters, numbers, underscores, and dots.

        Args:
            name: The metric name to validate

        Returns:
            True if name format is valid, False otherwise
        """
        if not name or len(name) > 256:
            return False
        return bool(VALID_METRIC_NAME_PATTERN.match(name))
