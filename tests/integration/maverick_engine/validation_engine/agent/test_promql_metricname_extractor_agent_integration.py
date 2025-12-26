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
from maverick_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


@pytest.mark.integration
class TestPromQLMetricNameExtractorAgentIntegration:

    @pytest.fixture
    def metrics_extractor_agent(self):
        config_manager = ConfigManager(expand_path("$HOME/.maverick_test"), "config.yml")
        instructions_manager = InstructionsManager()
        return PromQLMetricNameExtractorAgent(
            config_manager=config_manager,
            instructions_manager=instructions_manager
        )

    def test_promql_extractor_agent_integration_happy_path(self, metrics_extractor_agent):
        """
        Integration test for PromQLMetricNameExtractorAgent happy path.
        Verifies that the agent correctly processes an expression when the underlying LLM agent returns data.
        """
        # Execute
        expression = "rate(http.requests.total[5m]) + jvm.memory.used"
        result = metrics_extractor_agent.parse(expression)

        # Verify
        assert "http.requests.total" in result
        assert "jvm.memory.used" in result
