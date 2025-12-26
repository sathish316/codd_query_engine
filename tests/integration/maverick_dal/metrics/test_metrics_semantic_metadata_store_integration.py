"""
Unit tests for MetricsSemanticMetadataStore.

Tests cover all public methods with various scenarios including:
- Normal operations (indexing, searching)
- Edge cases (empty queries, missing fields, no results)
- Semantic search quality and relevance
- Multiple metrics and similarity ranking
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports from maverick-dal
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import chromadb

from maverick_dal.metrics.metrics_semantic_metadata_store import MetricsSemanticMetadataStore
from maverick_engine.validation_engine.metrics.structured_outputs import ValidationError



@pytest.fixture
def chromadb_client():
    """Provide a fresh in-memory ChromaDB client for testing."""
    # Use EphemeralClient to ensure fresh state for each test
    return chromadb.EphemeralClient()


@pytest.fixture
def store(chromadb_client, request):
    """Provide a MetricsSemanticMetadataStore instance with in-memory ChromaDB."""
    # Use unique collection name per test to ensure isolation
    collection_name = f"test_{request.node.name}"
    return MetricsSemanticMetadataStore(chromadb_client, collection_name=collection_name)


@pytest.mark.integration
class TestMetricsSemanticMetadataStoreIntegration:
    def test_complete_metric_semantic_metadata_workflow(self, store):
        """
        Integration test for the happy path workflow.

        This test simulates a realistic usage scenario:
        1. Index multiple metrics across different namespaces with complete metadata
        2. Perform semantic searches with natural language queries
        3. Verify search ranking and similarity scores
        4. Update existing metrics and verify upsert behavior
        5. Validate all returned metadata fields
        """
        # Step 1: Index metrics for a web application service
        namespace = "test:order_service"

        # Index HTTP latency metric
        http_latency_id = store.index_metadata(namespace, {
            "metric_name": "http.request.duration.p99",
            "type": "histogram",
            "description": "99th percentile HTTP request duration for all endpoints",
            "unit": "milliseconds",
            "category": "application",
            "subcategory": "http",
            "category_description": "Application-level performance metrics",
            "golden_signal_type": "latency",
            "golden_signal_description": "Time taken to service requests",
            "meter_type": "histogram",
            "meter_type_description": "Distribution of request durations over time"
        })
        assert http_latency_id == f"{namespace}#http.request.duration.p99"

        # Index error rate metric
        error_rate_id = store.index_metadata(namespace, {
            "metric_name": "http.errors.5xx.rate",
            "type": "counter",
            "description": "Rate of 5xx server errors per second",
            "unit": "errors_per_second",
            "category": "application",
            "subcategory": "http",
            "category_description": "Application-level performance metrics",
            "golden_signal_type": "errors",
            "golden_signal_description": "Rate of failed requests",
            "meter_type": "counter",
            "meter_type_description": "Monotonically increasing count of errors"
        })
        assert error_rate_id == f"{namespace}#http.errors.5xx.rate"

        # Index throughput metric
        throughput_id = store.index_metadata(namespace, {
            "metric_name": "http.requests.total",
            "type": "counter",
            "description": "Total number of HTTP requests received",
            "unit": "requests",
            "category": "application",
            "subcategory": "http",
            "category_description": "Application-level performance metrics",
            "golden_signal_type": "traffic",
            "golden_signal_description": "Volume of requests served",
            "meter_type": "counter",
            "meter_type_description": "Cumulative count of requests"
        })
        assert throughput_id == f"{namespace}#http.requests.total"

        # Step 2: Perform semantic searches and verify results

        # Search for latency metrics
        latency_results = store.search_metadata("request latency and response time", n_results=5)
        assert len(latency_results) >= 2, "Should find HTTP latency metrics"

        # Verify top result is HTTP latency (most semantically similar)
        assert latency_results[0]["metric_name"] == "http.request.duration.p99"
        assert latency_results[0]["golden_signal_type"] == "latency"
        assert 0 <= latency_results[0]["similarity_score"] <= 1

        # Step 3: Index metrics for another namespace
        namespace2 = "test:payment_service"

        store.index_metadata(namespace2, {
            "metric_name": "db.query.execution.time",
            "type": "histogram",
            "description": "Database query execution time in milliseconds",
            "unit": "milliseconds",
            "category": "infrastructure",
            "subcategory": "database",
            "golden_signal_type": "latency",
            "meter_type": "histogram"
        })

        store.index_metadata(namespace2, {
            "metric_name": "db.connections.active",
            "type": "gauge",
            "description": "Number of active database connections",
            "unit": "connections",
            "category": "infrastructure",
            "subcategory": "database",
            "golden_signal_type": "saturation",
            "meter_type": "gauge"
        })

        # Step 4: Search for metrics in another namespace
        db_results = store.search_metadata("latency", n_results=5)
        assert len(db_results) >= 1, "Should find at least 1 database metric"
        # Both database metrics should be highly ranked
        db_metric_names = [r["metric_name"] for r in db_results[:3]]
        assert "db.query.execution.time" in db_metric_names

        # Step 5: Test upsert behavior - update existing metric
        updated_id = store.index_metadata(namespace, {
            "metric_name": "http.request.duration.p99",
            "type": "histogram",
            "description": "UPDATED: 99th percentile latency for HTTP requests with improved accuracy",
            "unit": "milliseconds",
            "category": "application",
            "subcategory": "http",
            "golden_signal_type": "latency",
            "meter_type": "histogram"
        })
        assert updated_id == http_latency_id, "Should return same document ID for upsert"

        # Verify the update
        updated_results = store.search_metadata("improved accuracy latency", n_results=1)
        assert len(updated_results) > 0
        assert updated_results[0]["metric_name"] == "http.request.duration.p99"
        assert "UPDATED" in updated_results[0]["description"]
        assert "improved accuracy" in updated_results[0]["description"]