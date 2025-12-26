"""
PydanticAI-based PromQL query explainer and semantic validator.

This module provides an agent that explains what a generated PromQL query does
and validates whether it matches the original user intent semantically.
"""

import logging
from typing import Optional

from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.validation_engine.metrics.structured_outputs import SemanticValidationResult
from maverick_engine.utils.file_utils import expand_path

from opus_agent_base.agent.agent_builder import AgentBuilder
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

logger = logging.getLogger(__name__)


class SemanticValidationError(Exception):
    """Exception raised when semantic validation fails."""
    pass


class PromQLQueryExplainerAgent:
    """
    PromQL query explainer and semantic validator agent.

    Explains what a generated PromQL query does and compares it against
    the original intent to determine if they match semantically.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the PromQL query explainer agent.

        Args:
            config_manager: Configuration manager for agent settings
            instructions_manager: Manager for loading instruction prompts
        """
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager
        self._init_agent()

    def _init_agent(self):
        """Initialize the PromQL query explainer agent."""
        self.agent = (
            AgentBuilder(self.config_manager)
            .set_system_prompt_keys(["promql_query_explainer_agent_instruction"])
            .name("promql-query-explainer-agent")
            .add_instructions_manager(self.instructions_manager)
            .add_model_manager()
            .instruction(
                "promql_query_explainer_agent_instruction",
                expand_path("$HOME/.maverick/prompts/agent/metrics/PROMQL_QUERY_EXPLAINER_AGENT_INSTRUCTIONS.md")
            )
            .set_output_type(SemanticValidationResult)
            .build_simple_agent()
        )

    def _get_agent(self):
        """Get the underlying agent instance."""
        return self.agent

    def validate_semantic_match(
        self,
        original_intent: MetricsQueryIntent,
        generated_query: str
    ) -> SemanticValidationResult:
        """
        Validate whether a generated PromQL query matches the original intent.

        This method uses LLM intelligence to:
        1. Explain what the generated query actually does
        2. Summarize the original user intent
        3. Compare them semantically to determine if they match

        Args:
            original_intent: The original metrics query intent
            generated_query: The generated PromQL query string

        Returns:
            SemanticValidationResult with match status, explanation, and confidence

        Raises:
            SemanticValidationError: If validation process fails
        """
        # Guard: validate inputs
        if not generated_query or not generated_query.strip():
            logger.error("Empty generated query provided")
            raise SemanticValidationError("Generated query cannot be empty")

        if not original_intent.metric:
            logger.error("Original intent has no metric specified")
            raise SemanticValidationError("Original intent must specify a metric")

        # Format the validation prompt
        validation_prompt = self._format_validation_prompt(original_intent, generated_query)

        logger.info(
            f"Validating semantic match for metric: {original_intent.metric}",
            extra={
                "metric": original_intent.metric,
                "metric_type": original_intent.metric_type,
                "query_length": len(generated_query)
            }
        )

        # Execute LLM validation
        try:
            result = self._execute_validation(validation_prompt)

            logger.info(
                f"Semantic validation complete - Match: {result.intent_match}, Partial: {result.partial_match}, Confidence: {result.confidence:.2f}",
                extra={
                    "intent_match": result.intent_match,
                    "partial_match": result.partial_match,
                    "confidence": result.confidence,
                    "metric": original_intent.metric
                }
            )

            return result

        except Exception as e:
            logger.error(f"Semantic validation failed: {e}", exc_info=True)
            raise SemanticValidationError(
                f"Failed to validate query semantics: {e}"
            ) from e

    def _format_validation_prompt(
        self,
        original_intent: MetricsQueryIntent,
        generated_query: str
    ) -> str:
        """
        Format the validation prompt with intent and query details.

        Args:
            original_intent: The original metrics query intent
            generated_query: The generated PromQL query string

        Returns:
            Formatted prompt string for the LLM
        """
        # Format aggregation suggestions if present
        agg_suggestions_str = "None"
        if original_intent.aggregation_suggestions:
            agg_list = []
            for agg in original_intent.aggregation_suggestions:
                if agg.params:
                    params_str = ", ".join(f"{k}={v}" for k, v in agg.params.items())
                    agg_list.append(f"{agg.function_name}({params_str})")
                else:
                    agg_list.append(agg.function_name)
            agg_suggestions_str = ", ".join(agg_list)

        # Format filters if present
        filters_str = "None"
        if original_intent.filters:
            filters_str = ", ".join(f"{k}={v}" for k, v in original_intent.filters.items())

        # Format group by if present
        group_by_str = "None"
        if original_intent.group_by:
            group_by_str = ", ".join(original_intent.group_by)

        prompt = f"""Compare the following original query intent with the generated PromQL query:

**Original Intent:**
- Metric: {original_intent.metric}
- Metric Type: {original_intent.metric_type}
- Filters: {filters_str}
- Time Window: {original_intent.window}
- Group By: {group_by_str}
- Suggested Aggregations: {agg_suggestions_str}

**Generated PromQL Query:**
```promql
{generated_query}
```

Analyze whether the generated query semantically matches the original intent. Consider:
1. Does it query the correct metric?
2. Are filters correctly applied?
3. Is the time window appropriate?
4. Is the aggregation function suitable for the metric type and intent?
5. Are grouping dimensions correct?
6. Does the overall query achieve the user's goal?

Provide your analysis in the structured format."""

        return prompt

    def _execute_validation(self, prompt: str) -> SemanticValidationResult:
        """
        Execute the validation using the LLM agent.

        Args:
            prompt: The formatted validation prompt

        Returns:
            SemanticValidationResult from the LLM

        Raises:
            SemanticValidationError: If LLM execution fails
        """
        try:
            agent = self._get_agent()
            result = agent.run_sync(prompt)
            return result.output
        except Exception as e:
            raise SemanticValidationError(
                f"LLM validation execution failed: {e}"
            ) from e

