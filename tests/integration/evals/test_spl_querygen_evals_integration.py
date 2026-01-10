"""
Property-based integration tests for Splunk SPL query generation.

Tests multiple scenarios with different services, search patterns, indexes,
and sourcetypes to validate query generation works correctly across various cases.
"""

import pytest

from maverick_engine.logs.log_patterns import LogPattern
from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.agent.logs.spl_query_generator_agent import (
    SplunkSPLQueryGeneratorAgent,
)
from maverick_engine.validation_engine.logs.log_query_validator import (
    LogQueryValidator,
)
from maverick_engine.validation_engine.logs.syntax.splunk_syntax_validator import (
    SplunkSPLSyntaxValidator,
)
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


# Static test scenarios for Splunk SPL query generation
SPL_TEST_SCENARIOS = [
    {
        "id": "scenario_1_error_logs_single_pattern",
        "description": "Find error logs with single pattern",
        "intent": LogQueryIntent(
            description="Find error logs in payment service",
            backend="splunk",
            service="payment-service",
            patterns=[
                LogPattern(pattern="error", level="error"),
            ],
            default_level="error",
            limit=20,
        ),
        "expected_patterns": ["search", "error"],
    },
    {
        "id": "scenario_2_multiple_error_patterns",
        "description": "Multiple error patterns with different levels",
        "intent": LogQueryIntent(
            description="Find errors and exceptions in auth service",
            backend="splunk",
            service="auth-service",
            patterns=[
                LogPattern(pattern="error", level="error"),
                LogPattern(pattern="exception", level="error"),
                LogPattern(pattern="stack trace", level="error"),
            ],
            default_level="error",
            limit=20,
        ),
        "expected_patterns": ["search", "|"],
    },
    {
        "id": "scenario_3_database_errors",
        "description": "Find database-related errors",
        "intent": LogQueryIntent(
            description="Find database connection and query errors",
            backend="splunk",
            service="order-service",
            patterns=[
                LogPattern(pattern="database error", level="error"),
                LogPattern(pattern="connection pool exhausted", level="error"),
                LogPattern(pattern="query timeout", level="warn"),
            ],
            default_level="error",
            limit=20,
        ),
        "expected_patterns": ["search", "|"],
    },
    {
        "id": "scenario_4_authentication_failures",
        "description": "Find authentication and authorization issues",
        "intent": LogQueryIntent(
            description="Find auth failures and permission denied logs",
            backend="splunk",
            service="auth-service",
            patterns=[
                LogPattern(pattern="authentication failed", level="warn"),
                LogPattern(pattern="invalid token", level="warn"),
                LogPattern(pattern="permission denied", level="error"),
            ],
            default_level="warn",
            limit=20,
        ),
        "expected_patterns": ["search", "|"],
    },
]


#TODO: use LLM as judge or human feedback in addition to Regex to verify if generated query matches the intent
@pytest.mark.integration_querygen_evals
class TestSPLQueryGenEvalsIntegration:
    """Property-based tests for Splunk SPL query generation with static scenarios."""

    @pytest.fixture
    def config_manager(self):
        """Initialize ConfigManager for agents."""
        return ConfigManager(expand_path("$HOME/.maverick_test"), "config.yml")

    @pytest.fixture
    def instructions_manager(self):
        """Initialize InstructionsManager for agents."""
        return InstructionsManager()

    @pytest.fixture
    def splunk_syntax_validator(self):
        """Initialize Splunk SPL syntax validator."""
        return SplunkSPLSyntaxValidator()

    @pytest.fixture
    def log_query_validator(self, config_manager, splunk_syntax_validator):
        """Initialize Splunk SPL validator pipeline."""
        return LogQueryValidator(
            syntax_validators={"splunk": splunk_syntax_validator},
            config_manager=config_manager,
        )

    @pytest.fixture
    def query_generator(
        self,
        config_manager,
        instructions_manager,
        log_query_validator,
    ):
        """Initialize Splunk SPL query generator with all components."""
        return SplunkSPLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            log_query_validator=log_query_validator,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", SPL_TEST_SCENARIOS, ids=lambda s: s["id"])
    async def test_spl_query_generation_scenarios(
        self, scenario, query_generator
    ):
        """
        Property-based test: Generate Splunk SPL queries for multiple scenarios.

        Tests various combinations of:
        - Services (payment-service, auth-service, order-service)
        - Log patterns (error, exception, timeout, connection, database, auth)
        - Log levels (warn, error)
        - Limits (200 to 500 records)

        Each scenario validates:
        1. Query generation succeeds
        2. Generated query contains expected SPL patterns
        3. Query starts with 'search' keyword
        4. Query contains pipe commands for limiting results
        5. Service or pattern terms are referenced in query
        """
        print(f"\n{'='*80}")
        print(f"Testing Scenario: {scenario['id']}")
        print(f"Description: {scenario['description']}")
        print(f"Intent: {scenario['intent'].description}")
        print(f"Service: {scenario['intent'].service}")
        print(f"Patterns: {[p.pattern for p in scenario['intent'].patterns]}")
        print(f"{'='*80}")

        intent = scenario["intent"]

        # Act: Generate Splunk SPL query
        result = await query_generator.generate_query(intent)

        # Assert: Query generation succeeded
        assert result.success is True, (
            f"Scenario {scenario['id']} failed: {result.error}\n"
            f"Intent: {intent.description}"
        )

        # Assert: Query is not empty
        assert result.query is not None and len(result.query) > 0, (
            f"Scenario {scenario['id']} produced empty query"
        )

        # Assert: Query contains expected patterns
        query = result.query
        for pattern in scenario["expected_patterns"]:
            assert pattern in query.lower(), (
                f"Scenario {scenario['id']}: Expected pattern '{pattern}' not found in query.\n"
                f"Generated query: {query}"
            )

        # Assert: Query starts with 'search' keyword (Splunk convention)
        assert query.strip().lower().startswith("search"), (
            f"Scenario {scenario['id']}: SPL query should start with 'search' keyword.\n"
            f"Generated query: {query}"
        )

        # Assert: Query contains pipe command (typical SPL pattern)
        assert "|" in query, (
            f"Scenario {scenario['id']}: SPL query should contain pipe commands.\n"
            f"Generated query: {query}"
        )

        # Assert: Query contains head or limit command for result limiting
        has_limit = "head" in query.lower() or "limit" in query.lower() or "tail" in query.lower()
        assert has_limit, (
            f"Scenario {scenario['id']}: SPL query should contain result limiting command.\n"
            f"Generated query: {query}"
        )

        # Assert: Service or pattern terms are in query
        service_or_pattern_found = (
            intent.service in query.lower() or
            any(part in query.lower() for part in intent.service.split("-")) or
            any(p.pattern.split()[0].lower() in query.lower() for p in intent.patterns)
        )
        assert service_or_pattern_found, (
            f"Scenario {scenario['id']}: Neither service '{intent.service}' nor pattern terms "
            f"found in query.\nGenerated query: {query}"
        )

        print(f"✓ Scenario {scenario['id']} passed")
        print(f"  Generated query: {query}")
        print(f"  All expected patterns found: {scenario['expected_patterns']}")
