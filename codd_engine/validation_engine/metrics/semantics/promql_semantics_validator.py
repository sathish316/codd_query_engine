"""
Adapter for PromQL semantics validator to work with the Validator base class.

This module wraps the existing PromQLQueryExplainerAgent to make it compatible
with the abstract Validator interface for semantic validation.
"""

import logging

from codd_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from codd_engine.validation_engine.agent.metrics.promql_query_explainer_agent import (
    PromQLQueryExplainerAgent,
)
from codd_engine.validation_engine.metrics.semantics.metrics_semantics_validator import (
    MetricsSemanticsValidator,
)
from codd_engine.validation_engine.metrics.semantics.structured_outputs import (
    SemanticValidationResult,
)
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

logger = logging.getLogger(__name__)


class PromQLSemanticsValidator(MetricsSemanticsValidator):
    """
    Adapter that wraps PromQLQueryExplainerAgent to conform to the Validator interface.

    This adapter allows the existing semantic validator (query explainer agent)
    to be used in validation pipelines.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the semantics validator adapter.

        Args:
            config_manager: Configuration manager for agent settings
            instructions_manager: Manager for loading instruction prompts
        """
        self._config_manager = config_manager
        self._validator = PromQLQueryExplainerAgent(
            config_manager, instructions_manager
        )

    def validate(
        self, original_intent: MetricsQueryIntent, generated_query: str
    ) -> SemanticValidationResult:
        """
        Validate that the generated query semantically matches the original intent.

        Args:
            original_intent: The original metrics query intent
            generated_query: The generated PromQL query string

        Returns:
            SemanticValidationResult indicating whether query matches intent
        """
        # Get confidence threshold from config (default: 2, meaning scores 1-2 will fail)
        threshold = self._config_manager.get_setting(
            "mcp_config.metrics.promql.validation.semantics.confidence_threshold", 2
        )

        logger.debug(
            f"Validating semantics for metric '{original_intent.metric}': {generated_query[:100]}... (threshold: {threshold})"
        )
        return self._validator.validate_semantic_match(
            original_intent, generated_query, threshold
        )
