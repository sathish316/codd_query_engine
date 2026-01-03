"""Metrics client composing PromQL-specific operations."""

from maverick_mcp_server.config import MaverickConfig
from maverick_mcp_server.client.metrics_promql_client import MetricsPromQLClient
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    QueryGenerationResult,
)
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager
from maverick_engine.validation_engine.metrics.structured_outputs import SearchResult


class MetricsClient:
    """
    Client for metrics operations.

    Composes:
    - MetricsPromQLClient for PromQL query generation
    """

    def __init__(
        self,
        config: MaverickConfig,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the metrics client.

        Args:
            config: MaverickConfig instance
        """
        self.config = config
        self.promql = MetricsPromQLClient(config, config_manager, instructions_manager)

    def search_relevant_metrics(self, query: str, limit: int = 5) -> list[SearchResult]:
        """
        Search for metrics relevant to a query using semantic search.

        Args:
            query: Natural language query (e.g., "API experiencing high latency")
            limit: Maximum number of results to return

        Returns:
            List of metrics with similarity scores and metadata
        """
        return self.promql.search_relevant_metrics(query, limit)

    def construct_promql_query(
        self, intent: MetricsQueryIntent
    ) -> QueryGenerationResult:
        """
        Generate a valid PromQL query from metrics query intent.

        Args:
            intent: MetricsQueryIntent with query requirements

        Returns:
            QueryGenerationResult with final query and metadata
        """
        return self.promql.construct_promql_query(intent)
