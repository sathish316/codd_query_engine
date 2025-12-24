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


class TestMetricsSemanticMetadataStore:
    """Test suite for MetricsSemanticMetadataStore."""

    def test_index_metadata_basic(self, store):
        """Test indexing basic metric metadata."""
        metadata = {
            "metric_name": "cpu.usage",
            "type": "gauge",
            "description": "CPU utilization percentage",
            "unit": "percent",
            "category": "system",
            "subcategory": "cpu"
        }

        result = store.index_metadata(metadata)
        assert result == "cpu.usage"

    def test_index_metadata_all_fields(self, store):
        """Test indexing metadata with all schema fields."""
        metadata = {
            "metric_name": "http.request.duration",
            "type": "histogram",
            "description": "HTTP request duration in milliseconds",
            "unit": "ms",
            "category": "application",
            "subcategory": "http",
            "category_description": "Application-level metrics",
            "golden_signal_type": "latency",
            "golden_signal_description": "Measures request latency",
            "meter_type": "histogram",
            "meter_type_description": "Distribution of values over time"
        }

        result = store.index_metadata(metadata)
        assert result == "http.request.duration"

    def test_index_metadata_missing_required_field(self, store):
        """Test that indexing without metric_name raises KeyError."""
        metadata = {
            "type": "gauge",
            "description": "Some metric"
        }

        with pytest.raises(KeyError) as exc_info:
            store.index_metadata(metadata)
        assert "metric_name" in str(exc_info.value)

    def test_index_metadata_upsert(self, store):
        """Test that re-indexing same metric updates existing document."""
        namespace = "test_namespace"
        metric_name = "memory.usage"

        # Index first version
        metadata_v1 = {
            "metric_name": metric_name,
            "description": "Memory usage version 1",
            "category": "system"
        }
        store.index_metadata(namespace, metadata_v1)

        # Index updated version
        metadata_v2 = {
            "metric_name": metric_name,
            "description": "Memory usage version 2 updated",
            "category": "infrastructure"
        }
        result = store.index_metadata(namespace, metadata_v2)

        # Verify the update
        assert result == metric_name
        search_results = store.search_metadata("memory usage version 2", n_results=1)
        assert len(search_results) > 0
        assert search_results[0]["metric_name"] == metric_name
        assert "version 2" in search_results[0]["description"]

    def test_search_metadata_basic(self, store):
        """Test basic semantic search."""
        # Index some metrics
        store.index_metadata({
            "metric_name": "cpu.usage",
            "description": "CPU utilization percentage",
            "category": "system"
        })
        store.index_metadata({
            "metric_name": "memory.usage",
            "description": "Memory utilization in bytes",
            "category": "system"
        })

        # Search for CPU-related metrics
        results = store.search_metadata("CPU utilization")

        assert len(results) > 0
        assert results[0]["metric_name"] == "cpu.usage"
        assert "similarity_score" in results[0]
        assert 0 <= results[0]["similarity_score"] <= 1

    def test_search_metadata_no_results(self, store):
        """Test search with no indexed metrics returns empty list."""
        results = store.search_metadata("some query")
        assert results == []

    def test_search_metadata_ranking(self, store):
        """Test that search results are ranked by similarity."""
        # Index metrics with varying relevance
        store.index_metadata({
            "metric_name": "http.latency",
            "description": "HTTP request latency in milliseconds",
            "golden_signal_type": "latency"
        })
        store.index_metadata({
            "metric_name": "db.query.time",
            "description": "Database query execution time",
            "category": "database"
        })
        store.index_metadata({
            "metric_name": "network.bandwidth",
            "description": "Network bandwidth usage",
            "category": "network"
        })

        # Search for latency-related metrics
        results = store.search_metadata("request latency")

        assert len(results) > 0
        # Most relevant should be http.latency
        assert results[0]["metric_name"] == "http.latency"
        # Similarity scores should be in descending order
        for i in range(len(results) - 1):
            assert results[i]["similarity_score"] >= results[i + 1]["similarity_score"]

    def test_search_metadata_returns_all_fields(self, store):
        """Test that search results include all metadata fields."""
        metadata = {
            "metric_name": "test.metric",
            "type": "gauge",
            "description": "Test description",
            "unit": "bytes",
            "category": "test_category",
            "subcategory": "test_subcategory",
            "category_description": "Category desc",
            "golden_signal_type": "throughput",
            "golden_signal_description": "Measures throughput",
            "meter_type": "gauge",
            "meter_type_description": "Gauge meter"
        }
        store.index_metadata(metadata)

        results = store.search_metadata("test metric")

        assert len(results) > 0
        result = results[0]
        assert result["metric_name"] == "test.metric"
        assert result["type"] == "gauge"
        assert result["description"] == "Test description"
        assert result["unit"] == "bytes"
        assert result["category"] == "test_category"
        assert result["subcategory"] == "test_subcategory"
        assert result["category_description"] == "Category desc"
        assert result["golden_signal_type"] == "throughput"
        assert result["golden_signal_description"] == "Measures throughput"
        assert result["meter_type"] == "gauge"
        assert result["meter_type_description"] == "Gauge meter"

# TODO: remove redunant tests
    # def test_search_metadata_semantic_similarity(self, store):
    #     """Test that semantically similar queries find relevant metrics."""
    #     # Index metrics with specific semantics
    #     store.index_metadata({
    #         "metric_name": "error.rate",
    #         "description": "Rate of errors per second",
    #         "golden_signal_type": "errors",
    #         "category": "reliability"
    #     })
    #     store.index_metadata({
    #         "metric_name": "success.rate",
    #         "description": "Rate of successful requests",
    #         "golden_signal_type": "traffic",
    #         "category": "reliability"
    #     })

    #     # Search with semantically similar phrase
    #     results = store.search_metadata("failure count")

    #     # Should find error.rate as most relevant (errors and failures are semantically similar)
    #     assert len(results) > 0
    #     # error.rate should be ranked highly due to semantic similarity
    #     error_rate_found = any(r["metric_name"] == "error.rate" for r in results)
    #     assert error_rate_found

    # def test_search_metadata_category_search(self, store):
    #     """Test searching by category."""
    #     # Index metrics in different categories
    #     store.index_metadata({
    #         "metric_name": "cpu.usage",
    #         "description": "CPU usage",
    #         "category": "system",
    #         "subcategory": "cpu"
    #     })
    #     store.index_metadata({
    #         "metric_name": "http.requests",
    #         "description": "HTTP request count",
    #         "category": "application",
    #         "subcategory": "http"
    #     })

    #     # Search by category
    #     results = store.search_metadata("system metrics")

    #     assert len(results) > 0
    #     # cpu.usage should be highly ranked for system category query
    #     top_result = results[0]
    #     assert top_result["category"] in ["system", "application"]

    # def test_search_metadata_golden_signals(self, store):
    #     """Test searching by golden signal types."""
    #     # Index metrics with different golden signals
    #     store.index_metadata({
    #         "metric_name": "latency.p99",
    #         "description": "99th percentile latency",
    #         "golden_signal_type": "latency",
    #         "golden_signal_description": "Measures request latency"
    #     })
    #     store.index_metadata({
    #         "metric_name": "error.count",
    #         "description": "Total error count",
    #         "golden_signal_type": "errors",
    #         "golden_signal_description": "Tracks system errors"
    #     })
    #     store.index_metadata({
    #         "metric_name": "throughput",
    #         "description": "Requests per second",
    #         "golden_signal_type": "traffic",
    #         "golden_signal_description": "Measures request volume"
    #     })

    #     # Search for latency metrics
    #     results = store.search_metadata("response time performance")

    #     assert len(results) > 0
    #     # latency.p99 should be found due to semantic similarity
    #     latency_found = any(r["metric_name"] == "latency.p99" for r in results)
    #     assert latency_found

    # def test_multiple_metrics_same_category(self, store):
    #     """Test indexing and searching multiple metrics in same category."""
    #     # Index multiple CPU metrics
    #     for i in range(5):
    #         store.index_metadata({
    #             "metric_name": f"cpu.core{i}.usage",
    #             "description": f"CPU core {i} usage percentage",
    #             "category": "system",
    #             "subcategory": "cpu"
    #         })

    #     results = store.search_metadata("CPU core usage", n_results=10)

    #     assert len(results) == 5
    #     # All should be CPU metrics
    #     assert all("cpu.core" in r["metric_name"] for r in results)

    # def test_index_and_search_special_characters(self, store):
    #     """Test metrics with special characters in names and descriptions."""
    #     metadata = {
    #         "metric_name": "http.response.time.p95",
    #         "description": "HTTP response time (95th percentile) in ms",
    #         "unit": "ms",
    #         "category": "application/http"
    #     }
    #     store.index_metadata(metadata)

    #     results = store.search_metadata("95th percentile response")

    #     assert len(results) > 0
    #     assert results[0]["metric_name"] == "http.response.time.p95"

    # def test_index_empty_optional_fields(self, store):
    #     """Test that empty optional fields are handled gracefully."""
    #     metadata = {
    #         "metric_name": "test.metric",
    #         "description": "",
    #         "unit": "",
    #         "category": ""
    #     }

    #     result = store.index_metadata(metadata)
    #     assert result == "test.metric"

    #     # Search should still work
    #     search_results = store.search_metadata("test metric")
    #     # May or may not find it depending on embedding, but shouldn't error
    #     assert isinstance(search_results, list)

    # def test_collection_persistence_across_instances(self, chromadb_client):
    #     """Test that collection persists across store instances."""
    #     # Create first store and index data
    #     store1 = MetricsSemanticMetadataStore(chromadb_client)
    #     store1.index_metadata({
    #         "metric_name": "persistent.metric",
    #         "description": "Test persistence"
    #     })

    #     # Create second store with same client
    #     store2 = MetricsSemanticMetadataStore(chromadb_client)
    #     results = store2.search_metadata("persistent")

    #     # Should find the metric indexed by store1
    #     assert len(results) > 0
    #     assert any(r["metric_name"] == "persistent.metric" for r in results)

    # def test_different_collections_isolated(self, chromadb_client):
    #     """Test that different collections are isolated."""
    #     store1 = MetricsSemanticMetadataStore(chromadb_client, collection_name="collection1")
    #     store2 = MetricsSemanticMetadataStore(chromadb_client, collection_name="collection2")

    #     # Index to first collection
    #     store1.index_metadata({
    #         "metric_name": "metric1",
    #         "description": "In collection 1"
    #     })

    #     # Index to second collection
    #     store2.index_metadata({
    #         "metric_name": "metric2",
    #         "description": "In collection 2"
    #     })

    #     # Verify isolation
    #     results1 = store1.search_metadata("metric")
    #     results2 = store2.search_metadata("metric")

    #     metric1_names = [r["metric_name"] for r in results1]
    #     metric2_names = [r["metric_name"] for r in results2]

    #     assert "metric1" in metric1_names
    #     assert "metric1" not in metric2_names
    #     assert "metric2" in metric2_names
    #     assert "metric2" not in metric1_names

    # def test_large_batch_indexing(self, store):
    #     """Test indexing a large number of metrics."""
    #     # Index 100 metrics
    #     for i in range(100):
    #         store.index_metadata({
    #             "metric_name": f"metric.batch.{i}",
    #             "description": f"Batch metric number {i}",
    #             "category": "batch_test"
    #         })

    #     # Verify we can search and retrieve them
    #     results = store.search_metadata("batch metric", n_results=50)

    #     assert len(results) > 0
    #     assert len(results) <= 50
    #     assert all("metric.batch." in r["metric_name"] for r in results)

    # def test_unicode_in_metadata(self, store):
    #     """Test handling of unicode characters in metadata."""
    #     metadata = {
    #         "metric_name": "cpu.utilization.使用率",
    #         "description": "CPU utilization avec unicode: 使用率, émojis ❤️",
    #         "category": "système"
    #     }

    #     result = store.index_metadata(metadata)
    #     assert result == "cpu.utilization.使用率"

    #     # Search with unicode
    #     results = store.search_metadata("使用率")
    #     assert isinstance(results, list)

    # def test_search_with_no_indexed_data_different_queries(self, store):
    #     """Test various queries on empty collection."""
    #     queries = [
    #         "simple query",
    #         "query with numbers 123",
    #         "query-with-dashes",
    #         "query.with.dots"
    #     ]

    #     for query in queries:
    #         results = store.search_metadata(query)
    #         assert results == []


# class TestSecurityValidation:
#     """Security-focused tests for input validation and sanitization."""

#     def test_metric_name_too_long(self, store):
#         """Test that overly long metric names are rejected."""
#         long_name = "a" * 256  # Exceeds MAX_METRIC_NAME_LENGTH of 255
#         metadata = {"metric_name": long_name}

#         with pytest.raises(ValidationError) as exc_info:
#             store.index_metadata(metadata)
#         assert "exceeds maximum length" in str(exc_info.value)

#     def test_metric_name_invalid_characters(self, store):
#         """Test that metric names with invalid characters are rejected."""
#         invalid_names = [
#             "metric;name",  # semicolon
#             "metric name",  # space (should fail based on pattern)
#             "metric<script>",  # HTML tag
#             "metric|name",  # pipe
#             "metric&name",  # ampersand
#         ]

#         for invalid_name in invalid_names:
#             metadata = {"metric_name": invalid_name}
#             with pytest.raises(ValidationError) as exc_info:
#                 store.index_metadata(metadata)
#             assert "invalid characters" in str(exc_info.value).lower()

#     def test_metric_name_valid_characters(self, store):
#         """Test that metric names with valid characters are accepted."""
#         valid_names = [
#             "metric.name",
#             "metric-name",
#             "metric_name",
#             "metric/name",
#             "metric123",
#             "METRIC.NAME",
#         ]

#         for valid_name in valid_names:
#             metadata = {"metric_name": valid_name}
#             result = store.index_metadata(metadata)
#             assert result == valid_name

#     def test_text_field_too_long(self, store):
#         """Test that text fields exceeding maximum length are rejected."""
#         long_description = "a" * 2001  # Exceeds MAX_TEXT_FIELD_LENGTH of 2000
#         metadata = {
#             "metric_name": "test.metric",
#             "description": long_description
#         }

#         with pytest.raises(ValidationError) as exc_info:
#             store.index_metadata(metadata)
#         assert "exceeds maximum length" in str(exc_info.value)

#     def test_query_too_long(self, store):
#         """Test that overly long queries are rejected."""
#         long_query = "a" * 1001  # Exceeds MAX_QUERY_LENGTH of 1000

#         with pytest.raises(ValidationError) as exc_info:
#             store.search_metadata(long_query)
#         assert "exceeds maximum length" in str(exc_info.value)

#     def test_n_results_validation(self, store):
#         """Test that n_results is properly validated."""
#         store.index_metadata({
#             "metric_name": "test.metric",
#             "description": "Test"
#         })

#         # Test n_results < 1
#         with pytest.raises(ValidationError) as exc_info:
#             store.search_metadata("test", n_results=0)
#         assert "must be at least 1" in str(exc_info.value)

#         with pytest.raises(ValidationError):
#             store.search_metadata("test", n_results=-1)

#     def test_n_results_capped_at_maximum(self, store):
#         """Test that n_results exceeding maximum is capped."""
#         # Index some metrics
#         for i in range(10):
#             store.index_metadata({
#                 "metric_name": f"metric.{i}",
#                 "description": "Test metric"
#             })

#         # Request more than MAX_N_RESULTS (100)
#         results = store.search_metadata("test", n_results=200)

#         # Should be capped at maximum or number of indexed metrics, whichever is smaller
#         assert len(results) <= 100

#     def test_null_byte_sanitization(self, store):
#         """Test that null bytes are removed from input."""
#         metadata = {
#             "metric_name": "test.metric",
#             "description": "Test\x00description with null bytes\x00"
#         }

#         result = store.index_metadata(metadata)
#         assert result == "test.metric"

#         # Search and verify null bytes were sanitized
#         search_results = store.search_metadata("test description")
#         assert len(search_results) > 0
#         # Null bytes should be removed
#         assert "\x00" not in search_results[0]["description"]

#     def test_whitespace_sanitization(self, store):
#         """Test that excessive whitespace is normalized."""
#         metadata = {
#             "metric_name": "test.metric",
#             "description": "Test    description   with    excessive     whitespace"
#         }

#         store.index_metadata(metadata)
#         search_results = store.search_metadata("test description")

#         assert len(search_results) > 0
#         # Multiple spaces should be normalized to single space
#         assert "    " not in search_results[0]["description"]

#     def test_query_sanitization(self, store):
#         """Test that queries are properly sanitized."""
#         store.index_metadata({
#             "metric_name": "test.metric",
#             "description": "Test metric"
#         })

#         # Query with null bytes and excessive whitespace
#         query = "test   \x00   metric   with    spaces"
#         results = store.search_metadata(query)

#         # Should still work after sanitization
#         assert isinstance(results, list)

#     def test_empty_metric_name(self, store):
#         """Test that empty metric names are rejected."""
#         metadata = {"metric_name": ""}

#         with pytest.raises(ValidationError) as exc_info:
#             store.index_metadata(metadata)
#         assert "cannot be empty" in str(exc_info.value)

#     def test_metric_name_only_whitespace(self, store):
#         """Test that metric names with only whitespace are rejected."""
#         metadata = {"metric_name": "   "}

#         with pytest.raises(ValidationError):
#             store.index_metadata(metadata)

#     def test_sql_injection_like_input(self, store):
#         """Test handling of SQL injection-like patterns."""
#         # While ChromaDB doesn't use SQL, test that special characters are handled
#         metadata = {
#             "metric_name": "test.metric",
#             "description": "'; DROP TABLE metrics; --"
#         }

#         # Should not cause any errors
#         result = store.index_metadata(metadata)
#         assert result == "test.metric"

#         # Should be searchable
#         results = store.search_metadata("DROP TABLE")
#         assert isinstance(results, list)

#     def test_xss_like_input(self, store):
#         """Test handling of XSS-like patterns."""
#         metadata = {
#             "metric_name": "test.metric",
#             "description": "<script>alert('xss')</script>"
#         }

#         # Should not cause any errors
#         result = store.index_metadata(metadata)
#         assert result == "test.metric"

#         # Data should be stored as-is (sanitization handles control chars, not HTML)
#         results = store.search_metadata("script alert")
#         assert isinstance(results, list)


# class TestPerformanceOptimizations:
#     """Tests for performance optimizations."""

#     def test_caching_enabled(self, chromadb_client):
#         """Test that caching can be enabled."""
#         store = MetricsSemanticMetadataStore(chromadb_client, enable_caching=True)
#         assert store.enable_caching is True

#     def test_caching_disabled(self, chromadb_client):
#         """Test that caching can be disabled."""
#         store = MetricsSemanticMetadataStore(chromadb_client, enable_caching=False)
#         assert store.enable_caching is False

#     def test_cache_invalidation_on_index(self, chromadb_client):
#         """Test that cache is cleared when new data is indexed."""
#         # Use unique collection to avoid interference from other tests
#         store = MetricsSemanticMetadataStore(
#             chromadb_client,
#             collection_name="test_cache_invalidation",
#             enable_caching=True
#         )

#         # Index initial metric
#         store.index_metadata({
#             "metric_name": "metric1",
#             "description": "First metric"
#         })

#         # Search to populate cache
#         results1 = store.search_metadata("first")
#         assert len(results1) == 1

#         # Index new metric
#         store.index_metadata({
#             "metric_name": "metric2",
#             "description": "First and second metric"
#         })

#         # Search again - should find both metrics (cache cleared)
#         results2 = store.search_metadata("first")
#         # Should find at least the original metric (possibly both depending on relevance)
#         assert len(results2) >= 1

#     def test_collection_cosine_distance(self, chromadb_client):
#         """Test that collection is configured with cosine distance."""
#         store = MetricsSemanticMetadataStore(chromadb_client)

#         # Check collection metadata
#         collection_metadata = store.collection.metadata
#         assert "hnsw:space" in collection_metadata
#         assert collection_metadata["hnsw:space"] == "cosine"

#     def test_hnsw_parameters_configured(self, chromadb_client):
#         """Test that HNSW parameters are configured."""
#         store = MetricsSemanticMetadataStore(chromadb_client)

#         collection_metadata = store.collection.metadata
#         assert "hnsw:construction_ef" in collection_metadata
#         assert "hnsw:search_ef" in collection_metadata
#         assert "hnsw:M" in collection_metadata


# class TestErrorHandling:
#     """Tests for error handling and logging."""

#     def test_index_metadata_error_handling(self, store):
#         """Test error handling in index_metadata."""
#         # Try to index with invalid data type that will cause an error
#         with pytest.raises(KeyError):
#             store.index_metadata({})  # Missing metric_name

#     def test_search_metadata_error_handling_invalid_collection(self, chromadb_client):
#         """Test error handling when collection operations fail."""
#         store = MetricsSemanticMetadataStore(chromadb_client)

#         # Delete the collection to cause an error
#         chromadb_client.delete_collection(store.collection_name)

#         # Searching should raise an error
#         with pytest.raises(Exception):
#             store.search_metadata("test query")

#     def test_initialization_error_handling(self):
#         """Test error handling during initialization."""
#         # Try to initialize with invalid client
#         with pytest.raises(Exception):
#             MetricsSemanticMetadataStore(None)


# class TestTypeSafety:
#     """Tests for type hints and type safety."""

#     def test_metric_metadata_type_hints(self, store):
#         """Test that MetricMetadata type hints work correctly."""
#         from typing import get_type_hints

#         # Get type hints for index_metadata
#         hints = get_type_hints(store.index_metadata)
#         assert "metadata" in hints
#         assert "return" in hints

#     def test_search_result_type_hints(self, store):
#         """Test that SearchResult type hints work correctly."""
#         from typing import get_type_hints

#         # Get type hints for search_metadata
#         hints = get_type_hints(store.search_metadata)
#         assert "query" in hints
#         assert "n_results" in hints
#         assert "return" in hints
