"""Metrics client composing PromQL-specific operations."""

from maverick_lib.config import MaverickConfig
from maverick_lib.client.metrics_promql_client import MetricsPromQLClient
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent, QueryOpts
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
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance
        """
        self.config = config
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager
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

    async def construct_promql_query(
        self,
        intent: MetricsQueryIntent,
        namespace: str = "",
        bypass_cache: bool = False,
        query_opts: QueryOpts | None = None,
    ) -> QueryGenerationResult:
        """
        Generate a valid PromQL query from metrics query intent.

        Args:
            intent: MetricsQueryIntent with query requirements
            namespace: Optional namespace for schema validation
            bypass_cache: If True, skip cache lookup and force regeneration
            query_opts: Optional query options for controlling generation behavior

        Returns:
            QueryGenerationResult with final query and metadata
        """
        return await self.promql.construct_promql_query(
            intent, namespace, bypass_cache, query_opts
        )

    def metric_exists(self, namespace: str, metric_name: str) -> bool:
        """
        Check if a metric name exists in a namespace.

        Args:
            namespace: Namespace identifier
            metric_name: Metric name to check

        Returns:
            True if metric exists in namespace, False otherwise
        """
        return self.promql.metric_exists(namespace, metric_name)

    def get_all_metrics(self, namespace: str) -> list[str]:
        """
        Get all metric names in a namespace.

        Args:
            namespace: Namespace identifier

        Returns:
            List of metric names in the namespace
        """
        return self.promql.get_all_metrics(namespace)
