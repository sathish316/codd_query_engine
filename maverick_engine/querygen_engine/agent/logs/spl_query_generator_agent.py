"""
PydanticAI-based Splunk SPL query generator agent with ReAct pattern.

This module provides an agent that generates and validates Splunk SPL queries using
a custom validation tool in a ReAct (Reasoning + Acting) loop.
"""

import logging

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult,
    QueryGenerationError,
)
from maverick_engine.validation_engine.logs.log_query_validator import (
    LogQueryValidator,
)
from maverick_engine.querygen_engine.custom_tool.spl_validator_tool import (
    SplunkSPLValidatorTool,
)
from opus_agent_base.agent.agent_builder import AgentBuilder
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager
from pydantic import BaseModel, Field
from maverick_engine.utils.file_utils import expand_path

logger = logging.getLogger(__name__)


class SplunkSPLQueryResponse(BaseModel):
    """Response model for Splunk SPL query generation."""

    query: str = Field(..., description="The generated Splunk SPL query")
    reasoning: str = Field(
        ..., description="Explanation of query generation and refinements"
    )


class SplunkSPLQueryGeneratorAgent:
    """
    Splunk SPL query generator agent.

    Uses a custom validation tool to iteratively generate and refine queries
    until they pass all validation layers (syntax validation).
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
        log_query_validator: LogQueryValidator,
    ):
        """
        Initialize the Splunk SPL query generator agent.

        Args:
            config_manager: Configuration manager for agent settings
            instructions_manager: Manager for loading instruction prompts
            log_query_validator: Validator for Splunk SPL queries
        """
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager
        self.log_query_validator = log_query_validator
        self._init_agent()

    def _init_agent(self):
        """Initialize the Splunk SPL query generator agent with validation tool."""
        self.agent = (
            AgentBuilder(self.config_manager)
            .set_system_prompt_keys(["spl_query_generator_agent_instruction"])
            .name("spl-query-generator-agent")
            .add_instructions_manager(self.instructions_manager)
            .add_model_manager()
            .instruction(
                "spl_query_generator_agent_instruction",
                expand_path("$HOME/.maverick/prompts/agent/logs/SPLUNK_SPL_QUERY_GENERATOR_AGENT_INSTRUCTIONS.md"),
            )
            .set_output_type(SplunkSPLQueryResponse)
            .custom_tool(SplunkSPLValidatorTool(self.log_query_validator))
            .build_agent()
        )

    async def generate_query(self, intent: LogQueryIntent) -> QueryGenerationResult:
        """
        Generate a Splunk SPL query using ReAct pattern with validation tool.

        The agent will:
        1. Generate an initial query based on the intent
        2. Use the validate_spl_query tool to check the query
        3. If validation fails, adjust the query based on feedback
        4. Repeat until the query passes all validations or max iterations

        Args:
            intent: The log query intent

        Returns:
            QueryGenerationResult with final query and metadata

        Raises:
            QueryGenerationError: If query generation fails
        """
        logger.info(
            f"Starting query generation for intent: {intent.description}",
            extra={
                "description": intent.description,
                "backend": intent.backend,
                "service": intent.service,
                "patterns": [p.pattern for p in intent.patterns],
            },
        )

        try:
            # Format the generation prompt
            generation_prompt = self._format_generation_prompt(intent)

            # Execute LLM query generation with ReAct pattern
            logger.info("Executing agent with ReAct pattern")

            result = await self.agent.run(generation_prompt, deps=intent)

            logger.info(
                "Query generation completed",
                extra={
                    "description": intent.description,
                    "query": result.output.query,
                },
            )

            return QueryGenerationResult(
                query=result.output.query,
                success=True,
            )

        except Exception as e:
            logger.error(
                f"Query generation failed: {e}",
                exc_info=True,
                extra={"description": intent.description},
            )
            raise QueryGenerationError(
                f"Failed to generate Splunk SPL query for '{intent.description}': {e}"
            ) from e

    def _format_generation_prompt(self, intent: LogQueryIntent) -> str:
        """
        Format the generation prompt with intent details.

        Args:
            intent: The structured log query intent

        Returns:
            Formatted prompt string for the LLM
        """
        # Format patterns
        patterns_str = "None"
        if intent.patterns:
            patterns_list = []
            for pattern in intent.patterns:
                level_str = f" (level: {pattern.level})" if pattern.level else ""
                patterns_list.append(f'"{pattern.pattern}"{level_str}')
            patterns_str = ", ".join(patterns_list)

        prompt = f"""Generate a valid Splunk SPL query for the following log query intent:

**Log Query Intent:**
- Description: {intent.description}
- Backend: {intent.backend}
- Service: {intent.service or "None"}
- Log Patterns: {patterns_str}
- Default Level: {intent.default_level}
- Limit: {intent.limit}
- Namespace: {intent.namespace or "None"}

**IMPORTANT INSTRUCTIONS:**
1. Generate a Splunk SPL query that matches this intent
2. Use the `validate_spl_query` tool to validate your query
3. If validation fails, carefully read the feedback and fix the errors
4. Keep validating and refining until you get a valid query
5. The validation tool will check syntax correctness and provide feedback to fix the errors if required

Generate the best possible Splunk SPL query for the intent, then validate it using the tool."""

        return prompt
