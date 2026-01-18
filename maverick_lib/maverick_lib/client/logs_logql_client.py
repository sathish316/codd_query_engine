"""Client for LogQL operations - query generation."""

import logging
from typing import Optional

from maverick_lib.config import MaverickConfig
from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult,
)
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

from maverick_lib.client.provider import LogsModule, LogQLModule, CacheModule
from maverick_dal.cache import QuerygenCacheClient

logger = logging.getLogger(__name__)


class LogsLogQLClient:
    """
    Lean client for LogQL operations.

    Provides:
    - LogQL query generation from intent
    - Query execution against Loki
    - Label and label values retrieval
    """

    def __init__(
        self,
        config: MaverickConfig,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the LogQL client.

        Args:
            config: MaverickConfig instance
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance
        """
        self.config = config

        # Opus components
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager

        # LogQL validator (shared across all log backends)
        self.log_query_validator = LogsModule.get_log_query_validator(config_manager)

        # LogQL Query generator
        self._logql_query_generator = None

    @property
    def logql_query_generator(self):
        """Lazily initialize and return the LogQL query generator."""
        if self._logql_query_generator is None:
            self._logql_query_generator = LogQLModule.get_logql_query_generator(
                self.config_manager,
                self.instructions_manager,
                self.log_query_validator,
            )
        return self._logql_query_generator

    @property
    def querygen_cache_client(self) -> Optional[QuerygenCacheClient]:
        """Get the cache client if caching is enabled."""
        return CacheModule.get_querygen_cache_client(self.config)

    async def construct_logql_query(
        self, intent: LogQueryIntent, bypass_cache: bool = False
    ) -> QueryGenerationResult:
        """
        Generate a valid LogQL query from log query intent.

        Args:
            intent: LogQueryIntent with query requirements
            bypass_cache: If True, skip cache lookup and force regeneration

        Returns:
            QueryGenerationResult with final query and metadata
        """
        cache_client = self.querygen_cache_client
        namespace = intent.namespace or "default"

        # Log cache key for traceability
        if cache_client:
            querygen_cache_key = cache_client.get_querygen_cache_key(namespace, "logql", intent)
            logger.info("Processing LogQL query with querygen_cache_key=%s", querygen_cache_key)
        else:
            logger.info("No cache client found for LogQL query generator")

        # Check cache unless bypass is requested
        if cache_client and not bypass_cache:
            cached_query = cache_client.get_cached_query(
                namespace=namespace,
                query_type="logql",
                intent=intent,
            )
            if cached_query:
                logger.info("Cache hit for querygen_cache_key=%s", querygen_cache_key)
                return QueryGenerationResult(
                    query=cached_query,
                    success=True,
                    error=None,
                )

        # Generate query
        result = await self.logql_query_generator.generate_query(intent)

        # Cache successful results
        if cache_client and result.success and result.query:
            cache_client.cache_query(
                namespace=namespace,
                query_type="logql",
                intent=intent,
                query=result.query,
            )

        return result

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
