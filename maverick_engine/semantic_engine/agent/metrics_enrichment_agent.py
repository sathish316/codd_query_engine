"""
LLM-based agent for enriching metric metadata with semantic information.

This agent takes raw metric metadata from Prometheus and enriches it with:
- Detailed descriptions
- Categories and subcategories
- Golden signal classifications
- Meter type descriptions
"""

import logging
from typing import Optional

from maverick_engine.semantic_engine.structured_outputs import EnrichedMetricMetadata

from maverick_engine.models.metrics_common import MetricMetadata
from maverick_engine.utils.file_utils import expand_path

from opus_agent_base.agent.agent_builder import AgentBuilder
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


logger = logging.getLogger(__name__)


class MetricEnrichmentError(Exception):
    """Exception raised when metric enrichment fails."""

    pass


class MetricsEnrichmentAgent:
    """
    LLM-based agent for enriching metric metadata.

    Uses Claude Opus to analyze metric names and existing metadata to generate
    comprehensive semantic information for indexing into the semantic store.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the metrics enrichment agent.

        Args:
            config_manager: Configuration manager for agent settings
            instructions_manager: Manager for loading instruction prompts
        """
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager
        self._init_agent()

    def _init_agent(self):
        """Initialize the metrics enrichment agent."""
        self.agent = (
            AgentBuilder(self.config_manager)
            .set_system_prompt_keys(["metrics_enrichment_agent_instruction"])
            .name("metrics-enrichment-agent")
            .add_instructions_manager(self.instructions_manager)
            .add_model_manager()
            .instruction(
                "metrics_enrichment_agent_instruction",
                expand_path(
                    "$HOME/.maverick/prompts/agent/metrics/METRICS_ENRICHMENT_AGENT_INSTRUCTIONS.md"
                ),
            )
            .set_output_type(EnrichedMetricMetadata)
            .build_simple_agent()
        )

    def _get_agent(self):
        """Get the underlying agent instance."""
        return self.agent

    def enrich_metric(
        self,
        metric_name: str,
        metric_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> EnrichedMetricMetadata:
        """
        Enrich a metric with comprehensive semantic metadata.

        Args:
            metric_name: The name of the metric (e.g., "http_request_duration_seconds")
            metric_type: The Prometheus metric type (counter, gauge, histogram, summary)
            description: The description text from Prometheus HELP annotation

        Returns:
            EnrichedMetricMetadata with all semantic fields populated

        Raises:
            MetricEnrichmentError: If enrichment fails
        """
        if not metric_name or not metric_name.strip():
            logger.error("Empty metric name provided")
            raise MetricEnrichmentError("Metric name cannot be empty")

        prompt = self._format_enrichment_prompt(metric_name, metric_type, description)

        logger.debug(
            f"Enriching metric: {metric_name}",
            extra={
                "metric_name": metric_name,
                "metric_type": metric_type,
                "has_description": bool(description),
            },
        )

        try:
            result = self._execute_enrichment(prompt)

            # Ensure metric_name matches input
            result.metric_name = metric_name

            logger.debug(
                f"Metric enriched: {metric_name} -> category={result.category}, "
                f"golden_signal={result.golden_signal_type}",
                extra={
                    "metric_name": metric_name,
                    "category": result.category,
                    "subcategory": result.subcategory,
                    "golden_signal_type": result.golden_signal_type,
                },
            )

            return result

        except Exception as e:
            logger.error(
                f"Metric enrichment failed for {metric_name}: {e}", exc_info=True
            )
            raise MetricEnrichmentError(
                f"Failed to enrich metric '{metric_name}': {e}"
            ) from e

    def _format_enrichment_prompt(
        self, metric_name: str, metric_type: Optional[str], description: Optional[str]
    ) -> str:
        """
        Format the enrichment prompt for the LLM.

        Args:
            metric_name: The metric name
            metric_type: The Prometheus metric type
            description: The Prometheus description text

        Returns:
            Formatted prompt string
        """
        type_str = metric_type if metric_type else "unknown"
        description_str = description if description else "No description available"

        prompt = f"""Analyze and enrich the following metric with comprehensive semantic metadata:

**Metric Information:**
- Name: {metric_name}
- Type: {type_str}
- Description: {description_str}

**Your Task:**
Based on the metric name, type, and description, provide comprehensive semantic metadata including:

1. **Description**: A clear, detailed description of what this metric measures
2. **Unit**: The unit of measurement (e.g., milliseconds, bytes, percent, count, requests)
3. **Category**: High-level category (application, infrastructure, business, network, storage, etc.)
4. **Subcategory**: Specific area (http, database, cache, memory, cpu, disk, etc.)
5. **Category Description**: What this category represents
6. **Golden Signal Type**: Classify as latency, traffic, errors, saturation, or none
7. **Golden Signal Description**: How this relates to monitoring/observability
8. **Meter Type**: Classify as gauge, counter, histogram, or timer
9. **Meter Type Description**: What this meter type means for this specific metric

**Important Guidelines:**
- Infer meaning from metric naming conventions (e.g., _total suffix = counter, _seconds = latency)
- Use standard observability terminology
- Be specific and actionable in descriptions
- Consider the four golden signals of monitoring when classifying"""

        return prompt

    def _execute_enrichment(self, prompt: str) -> EnrichedMetricMetadata:
        """
        Execute the enrichment using the LLM agent.

        Args:
            prompt: The formatted enrichment prompt

        Returns:
            EnrichedMetricMetadata from the LLM

        Raises:
            MetricEnrichmentError: If LLM execution fails
        """
        try:
            agent = self._get_agent()
            result = agent.run_sync(prompt)
            return result.output
        except Exception as e:
            raise MetricEnrichmentError(f"LLM enrichment execution failed: {e}") from e

    def enrich_metric_to_dict(
        self,
        metric_name: str,
        metric_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> MetricMetadata:
        """
        Enrich a metric and return as MetricMetadata dictionary.

        This is a convenience method that returns the TypedDict format
        expected by the semantic metadata store.

        Args:
            metric_name: The name of the metric
            metric_type: The Prometheus metric type
            description: The description text from Prometheus

        Returns:
            MetricMetadata dictionary ready for indexing

        Raises:
            MetricEnrichmentError: If enrichment fails
        """
        enriched = self.enrich_metric(metric_name, metric_type, description)

        # Convert Pydantic model to MetricMetadata dict
        return MetricMetadata(
            metric_name=enriched.metric_name,
            type=enriched.type,
            description=enriched.description,
            unit=enriched.unit,
            category=enriched.category,
            subcategory=enriched.subcategory,
            category_description=enriched.category_description,
            golden_signal_type=enriched.golden_signal_type,
            golden_signal_description=enriched.golden_signal_description,
            meter_type=enriched.meter_type,
            meter_type_description=enriched.meter_type_description,
        )
