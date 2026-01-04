import logging
from opus_agent_base.tools.custom_tool import CustomTool
from maverick_engine.validation_engine.metrics.promql_validator import (
    PromQLValidator,
)
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.querygen_engine.metrics.structured_outputs import QueryGenerationContext
from maverick_engine.validation_engine.metrics.validation_result import ValidationResult
from pydantic_ai import RunContext

logger = logging.getLogger(__name__)


class PromQLValidatorTool(CustomTool):
    """
    Tool for validating PromQL queries with attempt tracking.
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
            ctx: RunContext[QueryGenerationContext],
            query: str,
            namespace: str = None,
            intent: MetricsQueryIntent = None,
            **kwargs,
        ) -> str:
            """
            Validate a PromQL query and track attempts.

            Args:
                ctx: The run context containing QueryGenerationContext
                query: The query string to validate
                namespace: The namespace to validate metrics against (optional, will use context if not provided)
                intent: The original query intent for semantic validation (optional, will use context if not provided)
                **kwargs: Additional keyword arguments required for validation

            Returns:
                str: Human-readable validation result message with attempt tracking
            """
            generation_context = ctx.deps

            # Use context values if not provided
            if namespace is None:
                namespace = generation_context.namespace
            if intent is None:
                intent = generation_context.intent

            current_attempt = generation_context.get_current_attempt_number() + 1

            logger.info(
                f"Validating PromQL query (attempt {current_attempt}/{generation_context.max_attempts}): {query}",
                extra={
                    "query": query,
                    "attempt": current_attempt,
                    "max_attempts": generation_context.max_attempts,
                },
            )

            # Check if we've reached max attempts BEFORE validation
            if generation_context.has_reached_max_attempts():
                error_msg = (
                    f"**MAX ATTEMPTS REACHED ({generation_context.max_attempts})**\n\n"
                    f"Unable to generate a valid query after {generation_context.max_attempts} attempts.\n\n"
                    f"**Attempt History:**\n{generation_context.get_attempt_history_summary()}\n\n"
                    f"Returning the best query from previous attempts."
                )
                logger.warning(error_msg)
                return error_msg

            # Perform validation
            validation_result = self.promql_validator.validate(
                namespace, query, intent, **kwargs
            )

            # Convert validation result to dict for storage
            validation_dict = {
                "is_valid": validation_result.is_valid,
                "error": validation_result.error,
            }

            # Add additional fields if present
            if hasattr(validation_result, "invalid_metrics"):
                validation_dict["invalid_metrics"] = validation_result.invalid_metrics
            if hasattr(validation_result, "intent_match"):
                validation_dict["intent_match"] = validation_result.intent_match
            if hasattr(validation_result, "partial_match"):
                validation_dict["partial_match"] = validation_result.partial_match
            if hasattr(validation_result, "explanation"):
                validation_dict["explanation"] = validation_result.explanation

            # Track this attempt
            generation_context.add_attempt(
                query=query,
                validation_result=validation_dict,
            )

            logger.info(
                f"Validation result (attempt {current_attempt}): {'Valid' if validation_result.is_valid else 'Invalid'}",
                extra={
                    "is_valid": validation_result.is_valid,
                    "error": validation_result.error,
                    "attempt": current_attempt,
                },
            )

            # Format response message
            if validation_result.is_valid:
                return (
                    f"**ALL VALIDATIONS PASSED** (Attempt {current_attempt})\n\n"
                    f"✓ Query is valid and ready to use!\n"
                    f"Query: {query}"
                )
            else:
                # Build detailed error message
                error_parts = [
                    f"**VALIDATION FAILED** (Attempt {current_attempt}/{generation_context.max_attempts})",
                    f"\nError: {validation_result.error}",
                ]

                # Add specific validation details
                if hasattr(validation_result, "invalid_metrics") and validation_result.invalid_metrics:
                    error_parts.append(f"Invalid metrics: {', '.join(validation_result.invalid_metrics)}")

                if hasattr(validation_result, "explanation") and validation_result.explanation:
                    error_parts.append(f"\nExplanation: {validation_result.explanation}")

                # Add attempt history if we have previous attempts
                if current_attempt > 1:
                    error_parts.append(f"\n**Previous Attempts:**\n{generation_context.get_attempt_history_summary()}")

                error_parts.append(
                    f"\nPlease fix the error and try again. You have {generation_context.max_attempts - current_attempt} attempts remaining."
                )

                return "\n".join(error_parts)
