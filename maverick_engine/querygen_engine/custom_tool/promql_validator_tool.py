import logging
from opus_agent_base.tools.custom_tool import CustomTool
from maverick_engine.validation_engine.metrics.promql_validator import (
    PromQLValidator,
)
from maverick_engine.validation_engine.metrics.schema.structured_outputs import SchemaValidationResult
from maverick_engine.validation_engine.metrics.semantics.structured_outputs import SemanticValidationResult
from maverick_engine.querygen_engine.metrics.structured_outputs import QueryGenerationInput
from pydantic_ai import RunContext

logger = logging.getLogger(__name__)


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
                error_msg = self._format_error_message(result, current_attempt, querygen_input)
                querygen_input.add_validation_result(error_msg)
                return error_msg

            # Success
            return f"**ALL VALIDATIONS PASSED**\n\n✓ Query is valid: {query}"

        def _format_error_message(
            self, result, current_attempt: int, querygen_input: QueryGenerationInput
        ) -> str:
            """Format validation error message."""
            parts = [
                f"**VALIDATION FAILED** (Attempt {current_attempt}/{querygen_input.max_attempts})",
                f"Error: {result.error}",
            ]

            # Add schema-specific details
            if isinstance(result, SchemaValidationResult) and result.invalid_metrics:
                parts.append(f"Invalid metrics: {', '.join(result.invalid_metrics)}")

            # Add semantic-specific details
            if isinstance(result, SemanticValidationResult):
                parts.append(f"Confidence: {result.confidence_score}/5")
                parts.append(f"Reasoning: {result.reasoning}")

            # Add validation history if we have previous attempts
            if current_attempt > 1:
                parts.append(querygen_input.get_validation_history())

            remaining = querygen_input.max_attempts - current_attempt
            parts.append(f"\nPlease fix the error. {remaining} attempts remaining.")

            return "\n".join(parts)
