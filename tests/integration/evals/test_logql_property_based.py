"""
Property-based integration tests for LogQL query generation.

Tests multiple scenarios with different services, log patterns, filters,
and levels to validate query generation works correctly across various cases.
"""

import pytest

from maverick_engine.logs.log_patterns import LogPattern
from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.agent.logs.logql_query_generator_agent import (
    LogQLQueryGeneratorAgent,
)
from maverick_engine.validation_engine.logs.log_query_validator import (
    LogQueryValidator,
)
from maverick_engine.validation_engine.logs.syntax.logql_syntax_validator import (
    LogQLSyntaxValidator,
)
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


# Static test scenarios for LogQL query generation
LOGQL_TEST_SCENARIOS = [
    {
        "id": "scenario_1_error_logs_single_pattern",
        "description": "Find error logs with single pattern",
        "intent": LogQueryIntent(
            description="Find error logs in payment service",
            backend="loki",
            service="payment-service",
            patterns=[
                LogPattern(pattern="error", level="error"),
            ],
            namespace="production",
            default_level="error",
            limit=200,
        ),
        "expected_patterns": ["{", "}", "service", "payment-service", "error"],
    },
    {
        "id": "scenario_2_multiple_error_patterns",
        "description": "Multiple error patterns with different levels",
        "intent": LogQueryIntent(
            description="Find errors and exceptions in auth service",
            backend="loki",
            service="auth-service",
            patterns=[
                LogPattern(pattern="error", level="error"),
                LogPattern(pattern="exception", level="error"),
                LogPattern(pattern="stack trace", level="error"),
            ],
            namespace="production",
            default_level="error",
            limit=500,
        ),
        "expected_patterns": ["{", "}", "auth-service"],
    },
    {
        "id": "scenario_3_timeout_warnings",
        "description": "Find timeout and connection issues",
        "intent": LogQueryIntent(
            description="Find timeout and connection warnings in API gateway",
            backend="loki",
            service="api-gateway",
            patterns=[
                LogPattern(pattern="timeout", level="warn"),
                LogPattern(pattern="connection refused", level="error"),
                LogPattern(pattern="connection reset", level="warn"),
            ],
            namespace="production",
            default_level="warn",
            limit=300,
        ),
        "expected_patterns": ["{", "}", "api-gateway"],
    },
    {
        "id": "scenario_4_database_errors",
        "description": "Find database-related errors",
        "intent": LogQueryIntent(
            description="Find database connection and query errors",
            backend="loki",
            service="order-service",
            patterns=[
                LogPattern(pattern="database error", level="error"),
                LogPattern(pattern="connection pool exhausted", level="error"),
                LogPattern(pattern="query timeout", level="warn"),
            ],
            namespace="production",
            default_level="error",
            limit=250,
        ),
        "expected_patterns": ["{", "}", "order-service"],
    },
    {
        "id": "scenario_5_authentication_failures",
        "description": "Find authentication and authorization issues",
        "intent": LogQueryIntent(
            description="Find auth failures and permission denied logs",
            backend="loki",
            service="auth-service",
            patterns=[
                LogPattern(pattern="authentication failed", level="warn"),
                LogPattern(pattern="invalid token", level="warn"),
                LogPattern(pattern="permission denied", level="error"),
            ],
            namespace="production",
            default_level="warn",
            limit=400,
        ),
        "expected_patterns": ["{", "}", "auth-service"],
    },
    {
        "id": "scenario_6_staging_environment",
        "description": "Query logs from staging environment",
        "intent": LogQueryIntent(
            description="Find errors in staging notification service",
            backend="loki",
            service="notification-service",
            patterns=[
                LogPattern(pattern="failed to send", level="error"),
                LogPattern(pattern="smtp error", level="error"),
            ],
            namespace="staging",
            default_level="error",
            limit=150,
        ),
        "expected_patterns": ["{", "}", "notification-service"],
    },
    {
        "id": "scenario_7_high_volume_query",
        "description": "High volume log query with multiple patterns",
        "intent": LogQueryIntent(
            description="Comprehensive error search across multiple patterns",
            backend="loki",
            service="inventory-service",
            patterns=[
                LogPattern(pattern="error", level="error"),
                LogPattern(pattern="warning", level="warn"),
                LogPattern(pattern="critical", level="fatal"),
                LogPattern(pattern="exception", level="error"),
                LogPattern(pattern="panic", level="fatal"),
            ],
            namespace="production",
            default_level="error",
            limit=1000,
        ),
        "expected_patterns": ["{", "}", "inventory-service"],
    },
]

#TODO: use LLM as judge with a completely different model to verify if generated query matches the intent
@pytest.mark.integration_querygen_evals
@pytest.mark.skip
class TestLogQLPropertyBased:
    """Property-based tests for LogQL query generation with static scenarios."""

    @pytest.fixture
    def config_manager(self):
        """Initialize ConfigManager for agents."""
        return ConfigManager(expand_path("$HOME/.maverick_test"), "config.yml")

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

    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", LOGQL_TEST_SCENARIOS, ids=lambda s: s["id"])
    async def test_logql_query_generation_scenarios(
        self, scenario, query_generator
    ):
        """
        Property-based test: Generate LogQL queries for multiple scenarios.

        Tests various combinations of:
        - Services (payment, auth, api-gateway, order, notification, inventory)
        - Log patterns (error, exception, timeout, connection, database, auth)
        - Log levels (debug, info, warn, error, fatal)
        - Namespaces (production, staging)
        - Limits (150 to 1000 records)

        Each scenario validates:
        1. Query generation succeeds
        2. Generated query contains expected patterns
        3. Query has valid LogQL structure (label selectors with braces)
        4. Service name is correctly referenced
        """
        print(f"\n{'='*80}")
        print(f"Testing Scenario: {scenario['id']}")
        print(f"Description: {scenario['description']}")
        print(f"Intent: {scenario['intent'].description}")
        print(f"Service: {scenario['intent'].service}")
        print(f"Patterns: {[p.pattern for p in scenario['intent'].patterns]}")
        print(f"{'='*80}")

        intent = scenario["intent"]

        # Act: Generate LogQL query
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
            assert pattern in query, (
                f"Scenario {scenario['id']}: Expected pattern '{pattern}' not found in query.\n"
                f"Generated query: {query}"
            )

        # Assert: Query has valid LogQL structure with label selectors
        assert "{" in query and "}" in query, (
            f"Scenario {scenario['id']}: Query missing LogQL label selector braces.\n"
            f"Generated query: {query}"
        )

        # Assert: Service name or service-related selector is in query
        service_found = (
            intent.service in query or
            "service" in query.lower() or
            any(part in query for part in intent.service.split("-"))
        )
        assert service_found, (
            f"Scenario {scenario['id']}: Service '{intent.service}' not referenced in query.\n"
            f"Generated query: {query}"
        )

        print(f"✓ Scenario {scenario['id']} passed")
        print(f"  Generated query: {query}")
        print(f"  All expected patterns found: {scenario['expected_patterns']}")
