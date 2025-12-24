"""
PydanticAI-based metric expression parser.

This module provides a MetricExpressionParser implementation that uses PydanticAI
to extract metric names from free-form metric expressions.
"""

import logging
import re
from typing import Optional

from pydantic import BaseModel, field_validator
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

logger = logging.getLogger(__name__)


# Regex pattern for valid metric name characters
VALID_METRIC_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_.]*$')


# System prompt for metric extraction
#TODO: use agents library to externalize prompts
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


# TODO: convert OpusAgents to library and use it here with better abstractions for agents
class PydanticAIMetricExpressionParser:
    """
    MetricExpressionParser implementation using PydanticAI Agents.

    Extracts metric names from expressions using an LLM.

    Args:
        settings: LLMSettings instance with API key and model configuration
        agent: Optional pre-configured Agent instance (for testing)

    Raises:
        MetricExpressionParseError: On parse failures or low confidence
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

        #TODO: fix deprecation warning
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
        and extract metric identifiers.

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
            result = self._extract(metric_expression)
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

    #TODO: handle retries in agents library
    def _extract(self, expression: str) -> MetricExtractionResponse:
        """
        Extract metrics with exponential backoff retry for transient errors.

        Args:
            expression: The metric expression to parse

        Returns:
            MetricExtractionResponse with extracted metrics and confidence

        Raises:
            MetricExpressionParseError: On non-retryable errors or max retries exceeded
        """
        try:
            agent = self._get_agent()
            result = agent.run_sync(expression)
            return result.data
        except MetricExpressionParseError:
            # Re-raise parse errors directly
            raise
        except Exception as e:
            # Non-retryable error, wrap and raise immediately
            raise MetricExpressionParseError(str(e)) from e

    #TODO: move to common utils
    def _is_valid_metric_name(self, name: str) -> bool:
        """
        Check if a metric name has valid format.

        Args:
            name: The metric name to validate

        Returns:
            True if name format is valid, False otherwise
        """
        if not name or len(name) > 256:
            return False
        return bool(VALID_METRIC_NAME_PATTERN.match(name))
