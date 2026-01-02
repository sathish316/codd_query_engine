"""Lean client for metrics operations - semantic search and PromQL query generation."""

from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent

from maverick_mcp_server.config import MaverickConfig
from maverick_mcp_server.client.promql_module import PromQLModule
from maverick_mcp_server.client.opus_module import OpusModule
from maverick_engine.querygen_engine.metrics.structured_outputs import (
    QueryGenerationResult,
)


class MetricsPromQLClient:
    """
    Lean client for metrics operations.

    Provides:
    - Semantic search for relevant metrics
    - PromQL query generation from intent
    """

    def __init__(self, config: MaverickConfig):
        """
        Initialize the metrics client.

        Args:
            config: MaverickConfig instance
        """
        self.config = config
        self.semantic_metadata_store = PromQLModule.get_semantic_store(config)
        self.metrics_metadata_store = PromQLModule.get_metrics_metadata_store(config)
        # Opus components
        self.config_manager = OpusModule.get_config_manager(config)
        self.instructions_manager = OpusModule.get_instructions_manager()
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
