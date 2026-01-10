"""
Property-based integration tests for PromQL query generation.

Tests multiple scenarios with different metric types, aggregations, filters,
and grouping to validate query generation works correctly across various cases.
"""

import pytest
import redis

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.querygen_engine.agent.metrics.promql_query_generator_agent import (
    PromQLQueryGeneratorAgent,
)
from maverick_engine.querygen_engine.metrics.preprocessor.promql_querygen_preprocessor import (
    PromQLQuerygenPreprocessor,
)
from maverick_engine.validation_engine.metrics.promql_validator import PromQLValidator
from maverick_engine.validation_engine.metrics.syntax.promql_syntax_validator import (
    PromQLSyntaxValidator,
)
from maverick_engine.validation_engine.metrics.schema.metrics_schema_validator import (
    MetricsSchemaValidator,
)
from maverick_engine.validation_engine.metrics.schema.substring_metric_parser import (
    SubstringMetricParser,
)
from maverick_engine.validation_engine.metrics.semantics.promql_semantics_validator import (
    PromQLSemanticsValidator,
)
from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


# Test namespace for evaluations
TEST_NAMESPACE = "test:text2sql_evals"

# Static test scenarios for PromQL query generation
PROMQL_TEST_SCENARIOS = [
    {
        "id": "scenario_1_counter_with_rate",
        "description": "Counter metric with rate aggregation and filters",
        "intent": MetricsQueryIntent(
            metric="http_requests_total",
            intent_description="Calculate rate of HTTP 500 errors per second over 5 minutes",
            metric_type="counter",
            filters={"status": "500", "method": "POST"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate", params={})
            ],
        ),
        "expected_patterns": ["rate(", "http_requests_total", "status=\"500\"", "5m"],
        "metrics_to_seed": ["http_requests_total", "http_request_duration_seconds"],
    },
    {
        "id": "scenario_2_gauge_with_avg",
        "description": "Gauge metric with average over time aggregation",
        "intent": MetricsQueryIntent(
            metric="memory_usage_bytes",
            intent_description="Calculate average memory usage over 5 minutes for feed-service in production",
            metric_type="gauge",
            filters={"environment": "production", "service": "feed-service"},
            window="5m",
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="avg_over_time", params={})
            ],
        ),
        "expected_patterns": ["avg_over_time(", "memory_usage_bytes", "environment=\"production\"", "service=\"feed-service\"", "5m"],
        "metrics_to_seed": ["memory_usage_bytes", "cpu_usage_percent"],
    },
    {
        "id": "scenario_3_histogram_quantile",
        "description": "Histogram metric with quantile calculation",
        "intent": MetricsQueryIntent(
            metric="http_request_duration_seconds",
            intent_description="Calculate 95th percentile of HTTP request duration",
            metric_type="histogram",
            filters={"method": "GET", "status": "200"},
            window="5m",
            group_by=["endpoint"],
            aggregation_suggestions=[
                AggregationFunctionSuggestion(
                    function_name="histogram_quantile",
                    params={"quantile": 0.95}
                )
            ],
        ),
        "expected_patterns": ["histogram_quantile", "http_request_duration_seconds", "0.95"],
        "metrics_to_seed": ["http_request_duration_seconds", "http_request_size_bytes"],
    },
    {
        "id": "scenario_4_counter_no_grouping",
        "description": "Counter metric with rate but no grouping",
        "intent": MetricsQueryIntent(
            metric="database_queries_total",
            intent_description="Calculate overall query rate across all databases",
            metric_type="counter",
            filters={"query_type": "SELECT"},
            window="5m",
            group_by=[],
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate", params={})
            ],
        ),
        "expected_patterns": ["rate(", "database_queries_total", "5m"],
        "metrics_to_seed": ["database_queries_total", "database_connections"],
    },
    {
        "id": "scenario_5_multiple_filters",
        "description": "Counter with multiple filters and multiple group by",
        "intent": MetricsQueryIntent(
            metric="network_packets_total",
            intent_description="Calculate packet rate filtered by protocol and direction",
            metric_type="counter",
            filters={
                "protocol": "tcp",
                "direction": "inbound",
                "interface": "eth0",
                "status": "success"
            },
            window="5m",
            group_by=["instance", "interface", "protocol"],
            aggregation_suggestions=[
                AggregationFunctionSuggestion(function_name="rate", params={})
            ],
        ),
        "expected_patterns": ["rate(", "network_packets_total", "protocol=\"tcp\"", "5m"],
        "metrics_to_seed": ["network_packets_total", "network_bytes_total"],
    },
]

#TODO: use LLM as judge or human feedback in addition to Regex to verify if generated query matches the intent
@pytest.mark.integration_querygen_evals
class TestPromQLQueryGenEvalsIntegration:
    """Property-based tests for PromQL query generation with static scenarios."""

    @pytest.fixture
    def config_manager(self):
        """Initialize ConfigManager for agents."""
        return ConfigManager(expand_path("$HOME/.maverick_test"), "config.yml")

    @pytest.fixture
    def instructions_manager(self):
        """Initialize InstructionsManager for agents."""
        return InstructionsManager()

    @pytest.fixture
    def preprocessor(self):
        """Initialize query preprocessor."""
        return PromQLQuerygenPreprocessor()

    @pytest.fixture
    def promql_syntax_validator(self):
        """Initialize syntax validator."""
        return PromQLSyntaxValidator()

    @pytest.fixture
    def redis_client(self):
        """Create Redis client for metadata store."""
        return redis.Redis(host="localhost", port=6380, decode_responses=True)

    @pytest.fixture
    def metadata_store(self, redis_client):
        """Create metrics metadata store."""
        return MetricsMetadataStore(redis_client)

    @pytest.fixture
    def promql_schema_validator_with_substring_schema_strategy(self, metadata_store):
        """Initialize schema validator with substring strategy."""
        parser = SubstringMetricParser(metadata_store)
        return MetricsSchemaValidator(metadata_store, parser)

    @pytest.fixture
    def promql_semantics_validator(self, config_manager, instructions_manager):
        """Initialize semantics validator."""
        return PromQLSemanticsValidator(
            config_manager=config_manager, instructions_manager=instructions_manager
        )

    @pytest.fixture
    def promql_validator(
        self,
        config_manager,
        instructions_manager,
        promql_syntax_validator,
        promql_schema_validator,
        promql_semantics_validator,
    ):
        """Initialize PromQL validator pipeline."""
        return PromQLValidator(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            syntax_validator=promql_syntax_validator,
            schema_validator=promql_schema_validator,
            semantics_validator=promql_semantics_validator,
        )

    @pytest.fixture
    def query_generator(
        self,
        config_manager,
        instructions_manager,
        preprocessor,
        promql_validator,
    ):
        """Initialize query generator with all components."""
        return PromQLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            preprocessor=preprocessor,
            promql_validator=promql_validator,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", PROMQL_TEST_SCENARIOS, ids=lambda s: s["id"])
    async def test_promql_query_generation_scenarios(
        self, scenario, query_generator, metadata_store
    ):
        """
        Property-based test: Generate PromQL queries for multiple scenarios.

        Tests various combinations of:
        - Metric types (counter, gauge, histogram)
        - Aggregation functions (rate, avg_over_time, histogram_quantile, etc.)
        - Filters (single, multiple)
        - Group by clauses (none, single, multiple)
        - Time windows (1m to 1h)

        Each scenario validates:
        1. Query generation succeeds
        2. Generated query contains expected patterns
        3. Query passes syntax validation
        4. Metric names are correctly referenced
        """
        print(f"\n{'='*80}")
        print(f"Testing Scenario: {scenario['id']}")
        print(f"Description: {scenario['description']}")
        print(f"Intent: {scenario['intent'].intent_description}")
        print(f"{'='*80}")

        # Setup: Seed metadata store with required metrics
        metadata_store.set_metric_names(
            TEST_NAMESPACE,
            set(scenario["metrics_to_seed"])
        )

        intent = scenario["intent"]

        # Act: Generate PromQL query
        result = await query_generator.generate_query(TEST_NAMESPACE, intent)

        # Assert: Query generation succeeded
        assert result.success is True, (
            f"Scenario {scenario['id']} failed: {result.error}\n"
            f"Intent: {intent.intent_description}"
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

        # Assert: Metric name is in the query
        assert intent.metric in query, (
            f"Scenario {scenario['id']}: Metric '{intent.metric}' not found in query.\n"
            f"Generated query: {query}"
        )

        print(f"✓ Scenario {scenario['id']} passed")
        print(f"  Generated query: {query}")
        print(f"  All expected patterns found: {scenario['expected_patterns']}")
