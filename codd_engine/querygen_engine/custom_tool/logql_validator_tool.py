import logging

from opus_agent_base.tools.custom_tool import CustomTool
from codd_engine.validation_engine.logs.log_query_validator import (
    LogQueryValidator,
)
from codd_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from codd_engine.validation_engine.logs.structured_outputs import (
    LogQueryValidationResult,
)
from pydantic_ai import RunContext

logger = logging.getLogger(__name__)


class LogQLValidatorTool(CustomTool):
    """
    Tool for validating LogQL queries.
    """

    def __init__(self, log_query_validator: LogQueryValidator):
        super().__init__(name="logql_validator_tool", config_key="logs.logql.validator")
        self.log_query_validator = log_query_validator

    def initialize_tools(self, agent):
        """Initialize the tool."""

        @agent.tool
        def validate_logql_query(
            ctx: RunContext[LogQueryValidationResult],
            query: str,
            backend: str = "loki",
            intent: LogQueryIntent = None,
            **kwargs,
        ) -> LogQueryValidationResult:
            """
            Validate a LogQL query.

            Args:
                query: The query string to validate
                backend: The backend to validate against (loki or splunk)
                intent: The original query intent for semantic validation (optional)
                **kwargs: Additional keyword arguments required for validation

            Returns:
                LogQueryValidationResult: A validation result indicating success or failure
            """
            logger.info(f"Validating {backend} query: {query}")

            # Extract description and patterns from intent if provided
            description = intent.description if intent else ""
            patterns = list(intent.patterns) if intent else []

            validation_result = self.log_query_validator.validate(
                backend=backend,
                query=query,
                description=description,
                patterns=patterns,
            )
            logger.info(f"Validation result: {validation_result}")
            return validation_result
