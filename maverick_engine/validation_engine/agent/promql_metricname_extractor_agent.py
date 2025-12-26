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

from maverick_engine.config.llm_settings import LLMSettings
from maverick_engine.validation_engine.metric_expression_parser import MetricExpressionParseError
from maverick_engine.validation_engine.structured_outputs import MetricExtractionResponse

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


class PromQLMetricNameExtractorAgent:
    """
    PromQL metric name extractor agent.

    Extracts metric names from PromQL expressions using an LLM.
    """

    def __init__(
        self,
        settings: LLMSettings,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        self._settings = settings
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager
        self._init_agent()

    def _init_agent(self):
        """Initialize the PromQL metric name extractor agent."""
        metrics_extractor_agent = (
            AgentBuilder(self.config_manager)
            .set_system_prompt_keys(["promql_metricname_extractor_agent_instruction"])
            .name("promql-metricname-extractor-agent")
            .add_instructions_manager(self.instructions_manager)
            .add_model_manager()
            .instruction(
                "promql_metricname_extractor_agent_instruction",
                expand_path("$HOME/.maverick/prompts/agent/PROMQL_METRICNAME_EXTRACTOR_AGENT_INSTRUCTIONS.md")
            )
            .build_simple_agent()
        )

    def extract(self, metric_expression: str) -> set[str]:
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

        # Convert to set and validate individual names
        metrics = set()
        for name in result.metric_names:
            if self._is_valid_metric_name(name):
                metrics.add(name)
            else:
                logger.warning(f"Skipping invalid metric name format: '{name}'")

        logger.info(
            f"Extracted {len(metrics)} metrics",
            extra={"metric_count": len(metrics)}
        )

        return metrics

    #TODO: handle retries in agents library
    def _extract_using_llm(self, expression: str) -> MetricExtractionResponse:
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
        if not name or len(name) > 256:
            return False
        return bool(VALID_METRIC_NAME_PATTERN.match(name))
