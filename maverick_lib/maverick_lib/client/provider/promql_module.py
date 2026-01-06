"""Dependency injection module for PromQL operations (Spring-like pattern)."""

import chromadb
import redis
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

from maverick_dal.metrics.metrics_semantic_metadata_store import (
    MetricsSemanticMetadataStore,
)
from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.querygen_engine.metrics.preprocessor.promql_querygen_preprocessor import (
    PromQLQuerygenPreprocessor,
)
from maverick_engine.validation_engine.metrics.syntax.promql_syntax_validator import (
    PromQLSyntaxValidator,
)
from maverick_engine.validation_engine.metrics.schema.metrics_schema_validator import (
    MetricsSchemaValidator,
)
from maverick_engine.validation_engine.metrics.promql_validator import (
    PromQLValidator,
)
from maverick_engine.querygen_engine.agent.metrics.promql_query_generator_agent import (
    PromQLQueryGeneratorAgent,
)
from maverick_engine.validation_engine.agent.metrics.promql_metricname_extractor_agent import (
    PromQLMetricNameExtractorAgent,
)
from maverick_engine.validation_engine.metrics.schema.metric_validation_strategy import (
    MetricValidationStrategy,
)
from maverick_engine.validation_engine.metrics.schema.substring_metric_parser import (
    SubstringMetricParser,
)
from maverick_engine.validation_engine.metrics.schema.fuzzy_metric_parser import (
    FuzzyMetricParser,
)
from maverick_lib.config import MaverickConfig
from maverick_engine.validation_engine.metrics.semantics.promql_semantics_validator import (
    PromQLSemanticsValidator,
)


class PromQLModule:
    """Module for PromQL operations - provides configured dependencies."""

    @classmethod
    def get_semantic_store(cls, config: MaverickConfig) -> MetricsSemanticMetadataStore:
        """
        Provide a configured MetricsSemanticMetadataStore instance.

        Args:
            config: MaverickConfig with semantic store configuration

        Returns:
            MetricsSemanticMetadataStore instance
        """
        chromadb_client = chromadb.HttpClient(
            host=config.semantic_store.chromadb_host,
            port=config.semantic_store.chromadb_port,
        )

        return MetricsSemanticMetadataStore(
            chromadb_client,
            collection_name=config.semantic_store.collection_name,
        )

    @classmethod
    def get_metrics_metadata_store(cls, config: MaverickConfig) -> MetricsMetadataStore:
        """
        Provide a MetricsMetadataStore instance.

        Args:
            config: MaverickConfig with Redis configuration

        Returns:
            MetricsMetadataStore instance
        """
        redis_client = cls._get_redis_client(config)
        return MetricsMetadataStore(redis_client)

    @classmethod
    def _get_redis_client(cls, config: MaverickConfig) -> redis.Redis:
        """
        Provide a configured Redis client instance.

        Args:
            config: MaverickConfig with Redis configuration

        Returns:
            redis.Redis instance
        """
        return redis.Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            decode_responses=config.redis.decode_responses,
        )

    @classmethod
    def get_promql_query_generator(
        cls,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
        promql_validator: PromQLValidator,
    ) -> PromQLQueryGeneratorAgent:
        """
        Provide a PromQLQueryGeneratorAgent instance.

        Args:
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance

        Returns:
            PromQLQueryGeneratorAgent instance
        """
        preprocessor = cls._get_metrics_query_preprocessor()

        return PromQLQueryGeneratorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            preprocessor=preprocessor,
            promql_validator=promql_validator,
        )

    @classmethod
    def _get_metrics_query_preprocessor(cls) -> PromQLQuerygenPreprocessor:
        """
        Provide a PromQLQuerygenPreprocessor instance.

        Returns:
            PromQLQuerygenPreprocessor instance
        """
        return PromQLQuerygenPreprocessor()

    @classmethod
    def get_promql_validator(
        cls,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
        metadata_store: MetricsMetadataStore,
    ) -> PromQLValidator:
        """
        Provide a PromQLValidator instance with all validators.

        Args:
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance
            metadata_store: MetricsMetadataStore instance

        Returns:
            PromQLValidator instance with syntax, schema, and semantics validators
        """
        syntax_validator = cls._get_promql_syntax_validator()

        schema_validator = cls._get_promql_metrics_schema_validator(
            metadata_store, config_manager, instructions_manager
        )

        semantics_validator = cls._get_promql_semantics_validator(
            config_manager, instructions_manager
        )

        return PromQLValidator(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            syntax_validator=syntax_validator,
            schema_validator=schema_validator,
            semantics_validator=semantics_validator,
        )

    @classmethod
    def _get_promql_syntax_validator(cls) -> PromQLSyntaxValidator:
        """
        Provide a PromQLSyntaxValidator instance.

        Returns:
            PromQLSyntaxValidator instance
        """
        return PromQLSyntaxValidator()

    @classmethod
    def _get_promql_metrics_schema_validator(
        cls,
        metadata_store: MetricsMetadataStore,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ) -> MetricsSchemaValidator:
        """
        Provide a MetricsSchemaValidator instance with the configured parser strategy.

        Args:
            metadata_store: MetricsMetadataStore instance
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance

        Returns:
            MetricsSchemaValidator instance with the appropriate metric parser
        """
        # Get the strategy from config (default to fuzzy)
        strategy_str = config_manager.get_setting(
            "mcp_config.metrics.promql.validation.schema.strategy", "fuzzy"
        ).lower()

        # Create the appropriate parser based on strategy
        if strategy_str == "llm":
            parser = cls._get_metric_extractor_agent(config_manager, instructions_manager)
        elif strategy_str == "substring":
            parser = SubstringMetricParser(metadata_store)
        elif strategy_str == "fuzzy":
            # Get fuzzy matching config parameters
            top_k = config_manager.get_setting(
                "mcp_config.metrics.promql.validation.schema.fuzzy.top_k", 10
            )
            min_similarity_score = config_manager.get_setting(
                "mcp_config.metrics.promql.validation.schema.fuzzy.min_similarity_score", 60
            )
            parser = FuzzyMetricParser(
                metadata_store,
                top_k=top_k,
                min_similarity_score=min_similarity_score,
            )
        else:
            # Fallback to fuzzy for invalid strategy
            parser = FuzzyMetricParser(metadata_store)

        return MetricsSchemaValidator(metadata_store, parser)

    @classmethod
    def _get_metric_extractor_agent(
        cls,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ) -> PromQLMetricNameExtractorAgent:
        """
        Provide a PromQLMetricNameExtractorAgent instance.

        Args:
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance

        Returns:
            PromQLMetricNameExtractorAgent instance
        """
        return PromQLMetricNameExtractorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
        )

    @classmethod
    def _get_promql_semantics_validator(
        cls,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
    ) -> PromQLSemanticsValidator:
        """
        Provide a PromQLSemanticsValidator instance.

        Args:
            config_manager: ConfigManager instance
            instructions_manager: InstructionsManager instance

        Returns:
            PromQLSemanticsValidator instance
        """
        return PromQLSemanticsValidator(
            config_manager=config_manager,
            instructions_manager=instructions_manager,
        )
