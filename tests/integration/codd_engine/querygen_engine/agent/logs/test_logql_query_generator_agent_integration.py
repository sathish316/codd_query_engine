"""
Integration tests for LogQL Query Generator Agent with ReAct pattern.

This test validates the end-to-end functionality of the LogQL query generator
with validation tool and iterative refinement.
"""

import pytest

from codd_engine.logs.log_patterns import LogPattern
from codd_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from codd_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult,
)
from codd_engine.querygen_engine.agent.logs.logql_query_generator_agent import (
    LogQLQueryGeneratorAgent,
)
from codd_engine.validation_engine.logs.log_query_validator import (
    LogQueryValidator,
)
from codd_engine.validation_engine.logs.syntax.logql_syntax_validator import (
    LogQLSyntaxValidator,
)
from codd_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


@pytest.mark.integration
@pytest.mark.integration_llm
class TestLogQLQueryGeneratorAgentIntegration:
    """Integration tests for LogQL query generator with ReAct pattern and validation tool."""

    @pytest.fixture
    def config_manager(self):
        """Initialize ConfigManager for agents."""
        return ConfigManager(expand_path("$HOME/.codd_test"), "config.yml")

    @pytest.fixture
    def instructions_manager(self):
        """Initialize InstructionsManager for agents."""
        return InstructionsManager()

    @pytest.fixture
    def logql_syntax_validator(self):
        """Initialize LogQL syntax validator."""
        return LogQLSyntaxValidator()

    @pytest.fixture
    def log_query_validator(self, config_manager, logql_syntax_validator):
        """Initialize LogQL validator pipeline."""
        return LogQueryValidator(
            syntax_validators={"loki": logql_syntax_validator},
            config_manager=config_manager,
        )

    @pytest.fixture
    def query_generator(
        self,
        config_manager,
        instructions_manager,
        log_query_validator,
    ):
        """Initialize LogQL query generator with all components."""
        return LogQLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            log_query_validator=log_query_validator,
        )

    async def test_generate_query_happy_path_simple_error_search(self, query_generator):
        """
        Integration test for happy path query generation with ReAct pattern.

        Tests the complete ReAct loop for generating a LogQL query for searching
        error logs in a service using the validation tool.

        Expected behavior:
        - Query should be generated successfully
        - Agent should use the validate_logql_query tool
        - Query should pass syntax validation
        - Final query should include service selector and error pattern filter

        Note: This test uses real LLM agents, so it will consume tokens.
        """
        # Arrange: Create user intent for searching error logs in payments service
        intent = LogQueryIntent(
            description="Find error logs in payments service",
            backend="loki",
            patterns=[LogPattern(pattern="error", level="error")],
            service="payments",
        )

        # Act: Generate query using ReAct pattern
        result = await query_generator.generate_query(intent)

        # Assert: Verify the generation succeeded
        print("\n=== Query Generation Result (ReAct Pattern) ===")
        print(f"Success: {result.success}")
        print(f"Final Query: {result.query}")
        if hasattr(result, "error") and result.error:
            print(f"Error: {result.error}")
        print("=" * 50)

        assert isinstance(result, QueryGenerationResult)
        assert result.success is True, (
            f"Expected successful generation but got failure. "
            f"Error: {getattr(result, 'error', 'Unknown error')}"
        )

        # Verify query structure and content
        assert result.query is not None and len(result.query) > 0
        assert "{" in result.query and "}" in result.query, (
            "Expected LogQL label selector with braces"
        )
        assert (
            'service="payments"' in result.query or "service=payments" in result.query
        ), "Expected service filter in query"
        assert "error" in result.query.lower(), "Expected error pattern in query"

        print(f"Final validated LogQL query: {result.query}")
