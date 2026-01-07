"""
PydanticAI-based PromQL query generator agent with ReAct pattern.

This module provides an agent that generates and validates PromQL queries using
a custom validation tool in a ReAct (Reasoning + Acting) loop.
"""

import logging

from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    PromQLQueryResponse,
    QueryGenerationResult,
    QueryGenerationError,
    QueryGenerationInput,
)
from maverick_engine.querygen_engine.metrics.preprocessor.metrics_querygen_preprocessor import (
    MetricsQuerygenPreprocessor,
)
from maverick_engine.validation_engine.metrics.promql_validator import (
    PromQLValidator,
)
from maverick_engine.utils.file_utils import expand_path
from maverick_engine.querygen_engine.custom_tool.promql_validator_tool import (
    PromQLValidatorTool,
)
from opus_agent_base.agent.agent_builder import AgentBuilder
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

logger = logging.getLogger(__name__)


class PromQLQueryGeneratorAgent:
    """
    PromQL query generator agent.

    Uses a custom validation tool to iteratively generate and refine queries
    until they pass all validation layers (syntax, schema, semantic).
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
        preprocessor: MetricsQuerygenPreprocessor,
        promql_validator: PromQLValidator,
    ):
        """
        Initialize the PromQL query generator agent.

        Args:
            config_manager: Configuration manager for agent settings
            instructions_manager: Manager for loading instruction prompts
            preprocessor: Preprocessor to enrich query intent
            promql_validator: Validator for PromQL
        """
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager
        self.preprocessor = preprocessor
        self.promql_validator = promql_validator
        self._init_agent()

    def _init_agent(self):
        """Initialize the PromQL query generator agent with validation tool."""
        self.agent = (
            AgentBuilder(self.config_manager)
            .set_system_prompt_keys(["promql_query_generator_agent_instruction"])
            .name("promql-query-generator-agent")
            .add_instructions_manager(self.instructions_manager)
            .add_model_manager()
            .instruction(
                "promql_query_generator_agent_instruction",
                expand_path(
                    "$HOME/.maverick/prompts/agent/metrics/PROMQL_QUERY_GENERATOR_AGENT_INSTRUCTIONS.md"
                ),
            )
            .set_output_type(PromQLQueryResponse)
            .custom_tool(PromQLValidatorTool(self.promql_validator))
            .build_agent()
        )

    async def generate_query(
        self, namespace: str, intent: MetricsQueryIntent
    ) -> QueryGenerationResult:
        """
        Generate a PromQL query using ReAct pattern with validation tool.

        The agent will:
        1. Generate an initial query based on the intent
        2. Use the validate_promql_query tool to check the query
        3. If validation fails, adjust the query based on feedback
        4. Repeat until the query passes all validations or max attempts reached

        Args:
            namespace: Namespace for schema validation
            intent: The metrics query intent

        Returns:
            QueryGenerationResult with final query, attempts, and metadata

        Raises:
            QueryGenerationError: If query generation fails
        """
        logger.info(
            f"Starting query generation for metric: {intent.metric}",
            extra={
                "metric": intent.metric,
                "metric_type": intent.metric_type,
                "filters": intent.filters,
                "window": intent.window,
                "namespace": namespace,
            },
        )

        try:
            # Preprocess intent
            preprocessed_intent = self.preprocessor.preprocess(intent)

            logger.info(
                "Intent preprocessed",
                extra={
                    "metric": preprocessed_intent.metric,
                    "aggregation_suggestions": [
                        agg.function_name
                        for agg in (preprocessed_intent.aggregation_suggestions or [])
                    ],
                },
            )

            # Get max_attempts from config (default: 5)
            max_attempts = self.config_manager.get_setting(
                "mcp_config.metrics.promql.generation.max_attempts", 5
            )

            # Create generation input with validation history tracking
            gen_input = QueryGenerationInput(
                namespace=namespace,
                intent=preprocessed_intent,
                max_attempts=max_attempts,
            )

            logger.info(
                f"Generation input created with max_attempts={max_attempts}",
                extra={"max_attempts": max_attempts},
            )

            # Format the generation prompt
            generation_prompt = self._format_generation_prompt(
                namespace, preprocessed_intent
            )

            # Execute LLM query generation with ReAct pattern
            logger.info("Executing agent with ReAct pattern")

            result = await self.agent.run(generation_prompt, deps=gen_input)

            logger.info(
                "Query generation completed",
                extra={
                    "metric": preprocessed_intent.metric,
                    "query": result.output.query,
                    "total_attempts": gen_input.get_attempt_count(),
                },
            )

            # Success if we have a query (validation errors are tracked in gen_input)
            return QueryGenerationResult(
                query=result.output.query,
                success=True,
                total_attempts=gen_input.get_attempt_count(),
            )

        except Exception as e:
            logger.error(
                f"Query generation failed: {e}",
                exc_info=True,
                extra={"metric": intent.metric},
            )
            raise QueryGenerationError(
                f"Failed to generate PromQL query for metric '{intent.metric}': {e}"
            ) from e

    def _format_generation_prompt(
        self, namespace: str, intent: MetricsQueryIntent
    ) -> str:
        """
        Format the generation prompt with intent details.

        Args:
            intent: The structured metrics query intent
            namespace: Optional namespace for schema validation

        Returns:
            Formatted prompt string for the LLM
        """
        # Format aggregation suggestions if present
        agg_suggestions_str = "None"
        if intent.aggregation_suggestions:
            agg_list = []
            for agg in intent.aggregation_suggestions:
                if agg.params:
                    params_str = ", ".join(f"{k}={v}" for k, v in agg.params.items())
                    agg_list.append(f"{agg.function_name}({params_str})")
                else:
                    agg_list.append(agg.function_name)
            agg_suggestions_str = ", ".join(agg_list)

        # Format filters if present
        filters_str = "None"
        if intent.filters:
            filters_str = ", ".join(f'{k}="{v}"' for k, v in intent.filters.items())

        # Format group by if present
        group_by_str = "None"
        if intent.group_by:
            group_by_str = ", ".join(intent.group_by)

        prompt = f"""Generate a valid PromQL query for the following metrics query intent:

**Metrics Query Intent:**
- Metric: {intent.metric}
- Intent description: {intent.intent_description}
- Metric Type: {intent.metric_type}
- Filters: {filters_str}
- Time Window: {intent.window}
- Group By: {group_by_str}
- Suggested Aggregations: {agg_suggestions_str}
- Namespace: {namespace}

Generate the best PromQL query that matches this intent. Use the suggested aggregations as guidance based on the metric type. After generating the query, validate it using the `validate_promql_query` tool by passing your generated query. If validation fails, adjust the query based on the feedback."""

        return prompt
