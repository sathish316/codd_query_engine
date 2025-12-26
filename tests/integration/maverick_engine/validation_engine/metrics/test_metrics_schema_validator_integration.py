"""
Integration tests for Validation Engine components.
"""
from unittest.mock import Mock, patch
import pytest
import redis

from maverick_engine.validation_engine.agent.promql_metricname_extractor_agent import (
    PromQLMetricNameExtractorAgent,
    MetricExtractionResponse
)
from maverick_engine.validation_engine.metrics.metrics_schema_validator import MetricsSchemaValidator
from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_engine.config.llm_settings import LLMSettings
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

@pytest.mark.integration
class TestMetricsSchemaValidatorIntegration:

    @pytest.fixture
    def metrics_extractor_agent(self):
        config_manager = ConfigManager(expand_path("$HOME/.maverick_test"), "config.yml")
        instructions_manager = InstructionsManager()
        return PromQLMetricNameExtractorAgent(
            settings=Mock(spec=LLMSettings),
            config_manager=config_manager,
            instructions_manager=instructions_manager
        )

    @pytest.fixture
    def redis_client(self):
        return redis.Redis(host="localhost", port=6380, decode_responses=True)

    @pytest.fixture
    def metadata_store(self, redis_client):
        return MetricsMetadataStore(redis_client)

    def test_schema_validator_integration_valid_metrics(
        self, 
        metrics_extractor_agent, 
        metadata_store
    ):
        """
        Integration test for MetricsSchemaValidator using MetricsExtractorAgent and MetricsMetadataStore.
        Verifies that:
        1. MetricsExtractorAgent extracts metrics from expression
        2. MetricsSchemaValidator checks these metrics against MetricsMetadataStore
        3. Returns valid result when metrics exist in store
        """
        # Seed valid metric names
        namespace = "test:order_service"
        metadata_store.set_metric_names(namespace, {"cpu.usage", "memory.free", "cpu.usage.max"})

        # Initialize MetricsSchemaValidator
        validator = MetricsSchemaValidator(metadata_store, metrics_extractor_agent)

        # Execute Validation
        expression = "cpu.usage / cpu.usage.max"
        result = validator.validate(namespace, expression)

        # Verify
        assert result.is_valid is True
        assert result.invalid_metrics == []

    def test_schema_validator_integration_invalid_metrics(
        self, 
        metrics_extractor_agent, 
        metadata_store
    ):
        """
        Integration test for MetricsSchemaValidator using MetricsExtractorAgent and MetricsMetadataStore.
        Verifies that:
        1. MetricsExtractorAgent extracts metrics from expression
        2. MetricsSchemaValidator checks these metrics against MetricsMetadataStore
        3. Returns valid result when metrics exist in store
        """
        # Seed valid metric names
        namespace = "test:order_service"
        metadata_store.set_metric_names(namespace, {"cpu.usage", "memory.free", "cpu.usage.max"})

        # Initialize MetricsSchemaValidator
        validator = MetricsSchemaValidator(metadata_store, metrics_extractor_agent)

        # Execute Validation
        expression = "memory.used + memory.free"
        result = validator.validate(namespace, expression)

        # Verify
        assert result.is_valid is False
        assert result.invalid_metrics == ["memory.used"]
