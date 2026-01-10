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
        "id": "scenario_1_simple_error_search",
        "description": "Simple error search in web logs",
        "intent": LogQueryIntent(
            description="Find error events in web application logs",
            backend="splunk",
            service="web-app",
            patterns=[
                LogPattern(pattern="error", level="error"),
            ],
            default_level="error",
            limit=100,
        ),
        "expected_patterns": ["search", "error", "head"],
    },
    {
        "id": "scenario_2_security_events",
        "description": "Security-related events search",
        "intent": LogQueryIntent(
            description="Find authentication failures and security violations",
            backend="splunk",
            service="security-service",
            patterns=[
                LogPattern(pattern="authentication failed", level="error"),
                LogPattern(pattern="unauthorized access", level="warn"),
                LogPattern(pattern="security violation", level="error"),
            ],
            default_level="error",
            limit=500,
        ),
        "expected_patterns": ["search", "|"],
    },
    {
        "id": "scenario_3_application_crashes",
        "description": "Application crash and panic search",
        "intent": LogQueryIntent(
            description="Find application crashes, panics, and fatal errors",
            backend="splunk",
            service="core-app",
            patterns=[
                LogPattern(pattern="panic", level="fatal"),
                LogPattern(pattern="segmentation fault", level="fatal"),
                LogPattern(pattern="fatal error", level="fatal"),
                LogPattern(pattern="application crashed", level="fatal"),
            ],
            default_level="fatal",
            limit=200,
        ),
        "expected_patterns": ["search", "head"],
    },
    {
        "id": "scenario_4_network_issues",
        "description": "Network connectivity and timeout issues",
        "intent": LogQueryIntent(
            description="Search for network timeouts, connection refused, and packet loss",
            backend="splunk",
            service="network-monitor",
            patterns=[
                LogPattern(pattern="connection timeout", level="error"),
                LogPattern(pattern="connection refused", level="error"),
                LogPattern(pattern="network unreachable", level="error"),
                LogPattern(pattern="packet loss", level="warn"),
            ],
            default_level="error",
            limit=300,
        ),
        "expected_patterns": ["search", "|"],
    },
    {
        "id": "scenario_5_database_operations",
        "description": "Database query and connection issues",
        "intent": LogQueryIntent(
            description="Find slow queries, connection pool issues, and deadlocks",
            backend="splunk",
            service="database-service",
            patterns=[
                LogPattern(pattern="slow query", level="warn"),
                LogPattern(pattern="deadlock detected", level="error"),
                LogPattern(pattern="connection pool exhausted", level="error"),
            ],
            default_level="warn",
            limit=400,
        ),
        "expected_patterns": ["search", "head"],
    },
    {
        "id": "scenario_6_api_errors",
        "description": "API gateway errors and rate limiting",
        "intent": LogQueryIntent(
            description="Search for API errors, rate limit exceeded, and gateway timeouts",
            backend="splunk",
            service="api-gateway",
            patterns=[
                LogPattern(pattern="rate limit exceeded", level="warn"),
                LogPattern(pattern="gateway timeout", level="error"),
                LogPattern(pattern="bad gateway", level="error"),
                LogPattern(pattern="service unavailable", level="error"),
            ],
            default_level="error",
            limit=600,
        ),
        "expected_patterns": ["search", "|"],
    },
    {
        "id": "scenario_7_payment_processing",
        "description": "Payment processing failures and transaction errors",
        "intent": LogQueryIntent(
            description="Find payment failures, declined transactions, and fraud alerts",
            backend="splunk",
            service="payment-processor",
            patterns=[
                LogPattern(pattern="payment failed", level="error"),
                LogPattern(pattern="transaction declined", level="warn"),
                LogPattern(pattern="fraud detected", level="error"),
                LogPattern(pattern="insufficient funds", level="warn"),
                LogPattern(pattern="payment gateway error", level="error"),
            ],
            default_level="error",
            limit=250,
        ),
        "expected_patterns": ["search", "head"],
    },
]


#TODO: use LLM as judge with a completely different model to verify if generated query matches the intent
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
        - Services (web-app, security, core-app, network, database, api-gateway, payment)
        - Search patterns (error, security, crashes, network, database, API, payment)
        - Log levels (debug, info, warn, error, fatal)
        - Limits (100 to 600 records)

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
