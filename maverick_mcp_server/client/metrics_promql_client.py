"""Lean client for metrics operations - semantic search and PromQL query generation."""

from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent

from maverick_mcp_server.config import MaverickConfig
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    QueryGenerationResult,
)
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

from maverick_mcp_server.client.provider.promql_module import PromQLModule


class MetricsPromQLClient:
    """
    Lean client for metrics operations.

    Provides:
    - Semantic search for relevant metrics
    - PromQL query generation from intent
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
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance
        """
        self.config = config
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager
        self.semantic_metadata_store = PromQLModule.get_semantic_store(config)
        self.metrics_metadata_store = PromQLModule.get_metrics_metadata_store(config)
        # Metrics PromQL Query Generator
        self.promql_validator = PromQLModule.get_promql_validator(
            self.config_manager, self.instructions_manager, self.metrics_metadata_store
        )
        # Query generator will be created lazily when needed
        self._promql_query_generator = None

    @property
    def promql_query_generator(self):
        """Lazily initialize and return the PromQL query generator."""
        if self._promql_query_generator is None:
            self._promql_query_generator = PromQLModule.get_promql_query_generator(
                self.config_manager, self.instructions_manager, self.promql_validator
            )
        return self._promql_query_generator

    def search_relevant_metrics(self, query: str, limit: int = 5) -> list[dict]:
        """
        Search for metrics relevant to a query using semantic search.

        Args:
            query: Natural language query (e.g., "API experiencing high latency")
            limit: Maximum number of results to return

        Returns:
            List of metrics with similarity scores and metadata
        """
        return self.semantic_metadata_store.search_metadata(query, n_results=limit)

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
        result = self.promql_query_generator.generate_query(intent)

        return result
