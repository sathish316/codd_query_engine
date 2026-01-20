"""Lean client for metrics operations - semantic search and PromQL query generation."""

import logging
from typing import Optional

from codd_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent, QueryOpts

from codd_lib.config import CoddConfig
from codd_engine.querygen_engine.metrics.structured_outputs import (
    QueryGenerationResult,
)
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager
from codd_engine.validation_engine.metrics.structured_outputs import SearchResult
from codd_lib.client.provider.promql_module import PromQLModule
from codd_lib.client.provider.cache_module import CacheModule
from codd_dal.cache import QuerygenCacheClient

logger = logging.getLogger(__name__)


class MetricsPromQLClient:
    """
    Lean client for metrics operations.

    Provides:
    - Semantic search for relevant metrics
    - PromQL query generation from intent
    """

    def __init__(
        self,
        config: CoddConfig,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the metrics client.

        Args:
            config: CoddConfig instance
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

    @property
    def querygen_cache_client(self) -> Optional[QuerygenCacheClient]:
        """Get the cache client if caching is enabled."""
        return CacheModule.get_querygen_cache_client(self.config)

    def search_relevant_metrics(self, query: str, limit: int = 5) -> list[SearchResult]:
        """
        Search for metrics relevant to a query using semantic search.

        Args:
            query: Natural language query (e.g., "API experiencing high latency")
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects with similarity scores and metadata
        """
        # Get raw results from semantic store
        raw_results = self.semantic_metadata_store.search_metadata(
            query, n_results=limit
        )

        # Convert to SearchResult TypedDict format
        search_results: list[SearchResult] = []
        for result in raw_results:
            search_result: SearchResult = {
                "metric_name": result.get("metric_name", ""),
                "similarity_score": result.get("similarity_score", 0.0),
                "description": result.get("description", ""),
                "unit": result.get("unit", ""),
                "category": result.get("category", ""),
                "subcategory": result.get("subcategory", ""),
                "category_description": result.get("category_description", ""),
                "golden_signal_type": result.get("golden_signal_type", ""),
                "golden_signal_description": result.get(
                    "golden_signal_description", ""
                ),
                "meter_type": result.get("meter_type", ""),
                "meter_type_description": result.get("meter_type_description", ""),
            }
            search_results.append(search_result)

        return search_results

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
        cache_client = self.querygen_cache_client

        # Log intent key for traceability
        if cache_client:
            querygen_cache_key = cache_client.get_querygen_cache_key(namespace, "promql", intent)
            logger.info("Processing PromQL query with querygen_cache_key=%s", querygen_cache_key)
        else:
            logger.info("No cache client found for PromQL query generator")

        # Check cache unless bypass is requested
        if cache_client and not bypass_cache:
            cached_query = cache_client.get_cached_query(
                namespace=namespace,
                query_type="promql",
                intent=intent,
            )
            if cached_query:
                return QueryGenerationResult(
                    query=cached_query,
                    success=True,
                    error=None,
                    total_attempts=0,
                )

        # Generate query
        result = await self.promql_query_generator.generate_query(
            namespace, intent, query_opts
        )

        # Cache successful results
        if cache_client and result.success and result.query:
            cache_client.cache_query(
                namespace=namespace,
                query_type="promql",
                intent=intent,
                query=result.query,
            )

        return result

    def metric_exists(self, namespace: str, metric_name: str) -> bool:
        """
        Check if a metric name exists in a namespace.

        Args:
            namespace: Namespace identifier
            metric_name: Metric name to check

        Returns:
            True if metric exists in namespace, False otherwise
        """
        return self.metrics_metadata_store.is_valid_metric_name(namespace, metric_name)

    def get_all_metrics(self, namespace: str) -> list[str]:
        """
        Get all metric names in a namespace.

        Args:
            namespace: Namespace identifier

        Returns:
            List of metric names in the namespace
        """
        metric_names = self.metrics_metadata_store.get_metric_names(namespace)
        return sorted(list(metric_names))
