"""Lean client for Splunk SPL operations - query generation."""

import logging
from typing import Optional

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import (
    QueryGenerationResult,
)

from maverick_lib.config import MaverickConfig
from maverick_lib.client.provider import LogsModule, SplunkModule, CacheModule
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager
from maverick_dal.cache import QuerygenCacheClient

logger = logging.getLogger(__name__)


class LogsSplunkClient:
    """
    Lean client for Splunk SPL operations.

    Provides:
    - Splunk SPL query generation from intent
    """

    def __init__(
        self,
        config: MaverickConfig,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ):
        """
        Initialize the Splunk SPL client.

        Args:
            config: MaverickConfig instance
        """
        self.config = config

        # Opus components
        self.config_manager = config_manager
        self.instructions_manager = instructions_manager

        # Log query validator (shared across all log backends)
        self.log_query_validator = LogsModule.get_log_query_validator(config_manager)

        # Query generator will be created lazily when needed
        self._spl_query_generator = None

    @property
    def spl_query_generator(self):
        """Lazily initialize and return the Splunk SPL query generator."""
        if self._spl_query_generator is None:
            self._spl_query_generator = SplunkModule.get_spl_query_generator(
                self.config_manager,
                self.instructions_manager,
                self.log_query_validator,
            )
        return self._spl_query_generator

    @property
    def querygen_cache_client(self) -> Optional[QuerygenCacheClient]:
        """Get the cache client if caching is enabled."""
        return CacheModule.get_querygen_cache_client(self.config)

    async def construct_spl_query(
        self, intent: LogQueryIntent, bypass_cache: bool = False
    ) -> QueryGenerationResult:
        """
        Generate a valid Splunk SPL query from log query intent.

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
            querygen_cache_key = cache_client.get_querygen_cache_key(namespace, "splunk", intent)
            logger.info("Processing Splunk query with querygen_cache_key=%s", querygen_cache_key)

        # Check cache unless bypass is requested
        if cache_client and not bypass_cache:
            cached_query = cache_client.get_cached_query(
                namespace=namespace,
                query_type="splunk",
                intent=intent,
            )
            if cached_query:
                return QueryGenerationResult(
                    query=cached_query,
                    success=True,
                    error=None,
                )

        # Generate query
        result = await self.spl_query_generator.generate_query(intent)

        # Cache successful results
        if cache_client and result.success and result.query:
            cache_client.cache_query(
                namespace=namespace,
                query_type="splunk",
                intent=intent,
                query=result.query,
            )

        return result

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
