import logging
from opus_agent_base.tools.custom_tool import CustomTool
from maverick_engine.validation_engine.metrics.promql_validator import (
    PromQLValidator,
)
from maverick_engine.querygen_engine.metrics.structured_outputs import QueryGenerationInput
from maverick_engine.validation_engine.metrics.validation_result import ValidationResultList
from pydantic_ai import RunContext

logger = logging.getLogger(__name__)

def format_validation_error_message(
    result: ValidationResultList, current_attempt: int, querygen_input: QueryGenerationInput
) -> str:
    """
    Format validation error message.

    ValidationResultList.error already formats all errors with stage names,
    so we just need to add attempt context.
    """
    parts = [
        f"**VALIDATION FAILED** (Attempt {current_attempt}/{querygen_input.max_attempts})",
        "",
        result.error,  # Already formatted with stage-specific errors
        "",
        f"Please fix the errors above. {querygen_input.max_attempts - current_attempt} attempts remaining.",
    ]

    return "\n".join(parts)


class PromQLValidatorTool(CustomTool):
    """
    Tool for validating PromQL queries with validation history tracking.
    """

    def __init__(self, promql_validator: PromQLValidator):
        super().__init__(
            name="promql_validator_tool", config_key="metrics.promql.validator"
        )
        self.promql_validator = promql_validator

    def initialize_tools(self, agent):
        """Initialize the tool."""

        @agent.tool
        def validate_promql_query(
            ctx: RunContext[QueryGenerationInput],
            query: str,
        ) -> str:
            """
            Validate a PromQL query and track validation history.

            Args:
                ctx: The run context containing QueryGenerationInput
                query: The query string to validate

            Returns:
                str: Human-readable validation result message
            """
            querygen_input = ctx.deps
            current_attempt = querygen_input.get_attempt_count() + 1

            logger.info(
                f"Validating PromQL query (attempt {current_attempt}/{querygen_input.max_attempts}): {query}",
                extra={
                    "query": query,
                    "attempt": current_attempt,
                    "max_attempts": querygen_input.max_attempts,
                },
            )

            # Check if max attempts reached
            if querygen_input.has_reached_max_attempts():
                error_msg = (
                    f"**MAX ATTEMPTS REACHED ({querygen_input.max_attempts})**\n\n"
                    f"Unable to generate a valid query after {querygen_input.max_attempts} attempts.\n\n"
                    f"{querygen_input.get_validation_history()}"
                )
                logger.warning(error_msg)
                return error_msg

            # Perform validation
            result = self.promql_validator.validate(
                querygen_input.namespace, query, querygen_input.intent
            )

            # Check for validation error (Go-style if err != nil)
            if result.error is not None:
                error_msg = format_validation_error_message(result, current_attempt, querygen_input)
                querygen_input.add_validation_result(error_msg)
                return error_msg

            # Success
            return f"**ALL VALIDATIONS PASSED**\n\n✓ Query is valid: {query}"
