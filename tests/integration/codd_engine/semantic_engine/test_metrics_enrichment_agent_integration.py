"""
Integration tests for Metrics Enrichment Agent.

This module tests the MetricsEnrichmentAgent's ability to enrich metric metadata
with semantic information using an LLM.
"""

import pytest

from codd_engine.semantic_engine.agent.metrics_enrichment_agent import (
    MetricsEnrichmentAgent,
)
from codd_engine.semantic_engine.structured_outputs import EnrichedMetricMetadata
from codd_engine.utils.file_utils import expand_path
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


@pytest.mark.integration
@pytest.mark.integration_llm
class TestMetricsEnrichmentAgentIntegration:
    @pytest.fixture
    def metrics_enrichment_agent(self):
        """Initialize the Metrics Enrichment Agent with real dependencies."""
        config_manager = ConfigManager(
            expand_path("$HOME/.codd_test"), "config.yml"
        )
        instructions_manager = InstructionsManager()
        return MetricsEnrichmentAgent(
            config_manager=config_manager, instructions_manager=instructions_manager
        )

    def test_enrich_http_request_duration_metric_happy_path(
        self, metrics_enrichment_agent: MetricsEnrichmentAgent
    ):
        """
        Integration test for the happy path of metrics enrichment.

        Tests enrichment of a common HTTP request duration metric (histogram type)
        with help text. This is a typical scenario for observability metrics.

        Expected behavior:
        - Returns EnrichedMetricMetadata with all required fields populated
        - Correctly identifies the metric as a latency/golden signal metric
        - Categorizes it under application/http
        - Identifies it as a histogram/timer meter type
        - Provides meaningful descriptions for all fields
        """
        # Arrange: Prepare metric information
        metric_name = "http_request_duration_seconds"
        metric_type = "histogram"
        description = "Duration of HTTP requests in seconds"

        # Act: Enrich the metric
        result = metrics_enrichment_agent.enrich_metric(
            metric_name=metric_name,
            metric_type=metric_type,
            description=description,
        )

        # Assert: Verify the enrichment result structure and content
        assert isinstance(result, EnrichedMetricMetadata)

        # Verify basic fields
        assert result.metric_name == metric_name
        assert result.type is not None and len(result.type) > 0
        assert result.description is not None and len(result.description) > 0

        # Verify unit field
        assert result.unit is not None
        assert (
            "second" in result.unit.lower()
            or "ms" in result.unit.lower()
            or "time" in result.unit.lower()
        )

        # Verify categorization
        assert result.category is not None and len(result.category) > 0
        assert result.subcategory is not None and len(result.subcategory) > 0
        assert (
            result.category_description is not None
            and len(result.category_description) > 0
        )

        # Verify golden signal classification (should be latency for duration metric)
        assert (
            result.golden_signal_type is not None and len(result.golden_signal_type) > 0
        )
        assert (
            result.golden_signal_description is not None
            and len(result.golden_signal_description) > 0
        )
        # HTTP duration should typically be classified as latency
        assert (
            "latency" in result.golden_signal_type.lower()
            or "latency" in result.golden_signal_description.lower()
        )

        # Verify meter type
        assert result.meter_type is not None and len(result.meter_type) > 0
        assert (
            result.meter_type_description is not None
            and len(result.meter_type_description) > 0
        )

        # Log the result for debugging
        print(f"\nEnrichment Result for {metric_name}:")
        print(f"  Description: {result.description}")
        print(f"  Unit: {result.unit}")
        print(f"  Category: {result.category} / {result.subcategory}")
        print(f"  Golden Signal: {result.golden_signal_type}")
        print(f"  Meter Type: {result.meter_type}")
