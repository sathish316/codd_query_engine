import logging
from opus_agent_base.tools.custom_tool import CustomTool
from maverick_engine.validation_engine.metrics.promql_validator import (
    PromQLValidator,
)
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.validation_engine.metrics.validation_result import ValidationResult
from pydantic_ai import RunContext

logger = logging.getLogger(__name__)


class PromQLValidatorTool(CustomTool):
    """
    Tool for validating PromQL queries.
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
            ctx: RunContext[ValidationResult],
            namespace: str,
            query: str,
            intent: MetricsQueryIntent = None,
            **kwargs,
        ) -> ValidationResult:
            """
            Validate a PromQL query.

            Args:
                namespace: The namespace to validate metrics against
                query: The query string to validate
                intent: The original query intent for semantic validation (optional)
                **kwargs: Additional keyword arguments required for validation

            Returns:
                ValidationResult: A ValidationResult (or subclass) indicating success or failure
            """
            logger.info(f"Validating PromQL query: {query}")
            validation_result = self.promql_validator.validate(
                namespace, query, intent, **kwargs
            )
            logger.info(f"Validation result: {validation_result}")
            return validation_result
