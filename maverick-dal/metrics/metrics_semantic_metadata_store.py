"""
ChromaDB-based semantic metadata store for metrics.

This module provides semantic search capabilities for metrics metadata using vector embeddings.
Unlike the Redis-based exact-match store, this enables natural language queries to find
similar metrics based on descriptions, categories, and other metadata.
"""

from typing import Optional, TypedDict
from functools import lru_cache
import re
import logging
import chromadb
from chromadb.config import Settings

# Configure logging
logger = logging.getLogger(__name__)

# Constants for input validation
MAX_METRIC_NAME_LENGTH = 255
MAX_TEXT_FIELD_LENGTH = 2000
MAX_QUERY_LENGTH = 1000
MAX_BULK_OPERATIONS = 1000
MAX_N_RESULTS = 100

# Metric name validation pattern (alphanumeric, dots, dashes, underscores, slashes, and unicode)
# Allow unicode characters for international support
METRIC_NAME_PATTERN = re.compile(r'^[\w._\-/]+$', re.UNICODE)


class MetricMetadata(TypedDict, total=False):
    """Type definition for metric metadata."""
    metric_name: str  # Required
    type: str
    description: str
    unit: str
    category: str
    subcategory: str
    category_description: str
    golden_signal_type: str
    golden_signal_description: str
    meter_type: str
    meter_type_description: str


class SearchResult(TypedDict):
    """Type definition for search results."""
    metric_name: str
    similarity_score: float
    type: str
    description: str
    unit: str
    category: str
    subcategory: str
    category_description: str
    golden_signal_type: str
    golden_signal_description: str
    meter_type: str
    meter_type_description: str


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class MetricsSemanticMetadataStore:
    """
    Client for managing metrics metadata with semantic search capabilities using ChromaDB.

    Provides methods to index and search metrics metadata using vector embeddings
    for natural language queries and semantic similarity.

    Args:
        chromadb_client: ChromaDB client instance (supports in-memory, persistent, or client-server modes)
        collection_name: Name of the ChromaDB collection (default: "metrics_semantic_metadata")
        enable_caching: Enable LRU caching for search queries (default: True)
    """

    def __init__(
        self,
        chromadb_client: chromadb.Client,
        collection_name: str = "metrics_semantic_metadata",
        enable_caching: bool = True
    ):
        """
        Initialize the metrics semantic metadata store.

        Args:
            chromadb_client: ChromaDB client instance for data operations
            collection_name: Name of the collection to use (default: "metrics_semantic_metadata")
            enable_caching: Enable LRU caching for search queries (default: True)
        """
        self.chromadb_client = chromadb_client
        self.collection_name = collection_name
        self.enable_caching = enable_caching
        self._search_cache = {}  # Simple cache for search results

        try:
            # Get or create the collection with optimized settings
            # Use cosine distance for semantic similarity (normalized dot product)
            # Configure HNSW index for better performance
            self.collection = self.chromadb_client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",  # Cosine similarity for semantic search
                    "hnsw:construction_ef": 200,  # Higher quality index construction
                    "hnsw:search_ef": 100,  # Balance between speed and accuracy
                    "hnsw:M": 16  # Number of connections per element
                }
            )
            logger.info(f"Initialized collection '{self.collection_name}' with cosine distance metric")
        except Exception as e:
            logger.error(f"Failed to initialize collection '{self.collection_name}': {e}")
            raise

    def _validate_metric_name(self, metric_name: str) -> None:
        """
        Validate metric name format and length.

        Args:
            metric_name: Metric name to validate

        Raises:
            ValidationError: If metric name is invalid
        """
        if not metric_name:
            raise ValidationError("metric_name cannot be empty")

        if len(metric_name) > MAX_METRIC_NAME_LENGTH:
            raise ValidationError(
                f"metric_name exceeds maximum length of {MAX_METRIC_NAME_LENGTH} characters"
            )

        if not METRIC_NAME_PATTERN.match(metric_name):
            raise ValidationError(
                f"metric_name contains invalid characters. "
                f"Only alphanumeric, dots, dashes, underscores, and slashes are allowed"
            )

    def _validate_text_field(self, field_name: str, field_value: str) -> None:
        """
        Validate text field length.

        Args:
            field_name: Name of the field being validated
            field_value: Value to validate

        Raises:
            ValidationError: If field value exceeds maximum length
        """
        if field_value and len(field_value) > MAX_TEXT_FIELD_LENGTH:
            raise ValidationError(
                f"{field_name} exceeds maximum length of {MAX_TEXT_FIELD_LENGTH} characters"
            )

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text input by removing potentially problematic characters.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove null bytes and control characters
        sanitized = text.replace('\x00', '').strip()

        # Replace multiple whitespaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)

        return sanitized

    def index_metadata(self, metadata: MetricMetadata) -> str:
        """
        Index metric metadata for semantic search.

        Creates a searchable document by combining key metadata fields and stores
        all metadata for retrieval. Uses metric_name as document ID for upsert semantics
        (re-indexing the same metric updates existing document).

        Args:
            metadata: Dictionary containing metric metadata with required field:
                     - metric_name (str): Unique identifier for the metric
                     Optional fields:
                     - type (str): Metric type
                     - description (str): Metric description
                     - unit (str): Unit of measurement
                     - category (str): High-level category
                     - subcategory (str): Sub-category
                     - category_description (str): Description of category
                     - golden_signal_type (str): Golden signal classification
                     - golden_signal_description (str): Golden signal description
                     - meter_type (str): Type of meter/instrument
                     - meter_type_description (str): Meter type description

        Returns:
            Document ID (same as metric_name)

        Raises:
            ValidationError: If metric_name is invalid or fields exceed length limits
            KeyError: If metric_name is not provided in metadata
        """
        if "metric_name" not in metadata:
            raise KeyError("metric_name is required in metadata")

        metric_name = str(metadata["metric_name"])

        # Validate metric name
        self._validate_metric_name(metric_name)

        # Define text fields to validate
        text_fields = [
            "type", "description", "unit", "category", "subcategory",
            "category_description", "golden_signal_type", "golden_signal_description",
            "meter_type", "meter_type_description"
        ]

        # Validate all text fields
        for field_name in text_fields:
            field_value = metadata.get(field_name, "")
            if field_value:
                self._validate_text_field(field_name, str(field_value))

        # Clear cache when indexing new data
        if self.enable_caching and hasattr(self, '_search_cache'):
            self._search_cache.clear()

        try:
            # Create searchable document text by combining key fields
            # Use list comprehension for better performance
            document_parts = [
                self._sanitize_text(str(metadata.get(field, "")))
                for field in ["description", "category", "subcategory",
                             "golden_signal_type", "meter_type"]
                if metadata.get(field)
            ]

            # Add labels for better semantic context
            labeled_parts = []
            field_labels = {
                "category": "Category",
                "subcategory": "Subcategory",
                "golden_signal_type": "Golden Signal",
                "meter_type": "Meter Type"
            }

            for field, label in field_labels.items():
                if metadata.get(field):
                    labeled_parts.append(f"{label}: {self._sanitize_text(str(metadata[field]))}")

            # Combine description with labeled fields
            if metadata.get("description"):
                document_parts = [self._sanitize_text(str(metadata["description"]))] + labeled_parts
            else:
                document_parts = labeled_parts

            document_text = " | ".join(document_parts) if document_parts else metric_name

            # Extract all metadata fields for storage using dict comprehension
            metadata_dict = {
                field: self._sanitize_text(str(metadata.get(field, "")))
                for field in text_fields
            }

            # Upsert document to collection (updates if exists, adds if new)
            self.collection.upsert(
                documents=[document_text],
                metadatas=[metadata_dict],
                ids=[metric_name]
            )

            logger.debug(f"Indexed metric: {metric_name}")
            return metric_name

        except Exception as e:
            logger.error(f"Failed to index metric '{metric_name}': {e}")
            raise

    def _cached_search(self, query: str, n_results: int) -> list[SearchResult]:
        """
        Internal cached search method.

        Args:
            query: Sanitized search query
            n_results: Number of results to return

        Returns:
            List of search results
        """
        try:
            # Query the collection for similar documents
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )

            # Parse and format results using zip for better performance
            formatted_results = []

            if results["ids"] and results["ids"][0]:
                ids = results["ids"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []

                # Use zip for optimized iteration over parallel lists
                for metric_name, metadata, distance in zip(ids, metadatas, distances):
                    result_dict = {
                        "metric_name": metric_name,
                        "similarity_score": 1 - distance,
                        **metadata  # Unpack metadata fields directly
                    }
                    formatted_results.append(result_dict)

            logger.debug(f"Search query '{query}' returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search query failed for '{query}': {e}")
            raise

    def search_metadata(self, query: str, n_results: int = 10) -> list[SearchResult]:
        """
        Search for metrics using semantic similarity.

        Performs vector similarity search to find metrics most relevant to the query.
        Results are ranked by semantic similarity. Supports LRU caching for repeated queries.

        Args:
            query: Natural language search query
            n_results: Maximum number of results to return (default: 10, max: 100)

        Returns:
            List of dictionaries containing metric information and similarity scores.
            Each dictionary contains:
            - metric_name (str): The metric identifier
            - similarity_score (float): Similarity score between 0 and 1 (higher is more similar)
            - All metadata fields (type, description, unit, etc.)

        Raises:
            ValidationError: If query is too long or n_results exceeds maximum

        Note:
            Returns empty list if no metrics are indexed or query returns no results.
        """
        # Validate empty query
        if not query or not query.strip():
            logger.debug("Empty query received, returning empty results")
            return []

        # Sanitize and validate query
        sanitized_query = self._sanitize_text(query)

        if len(sanitized_query) > MAX_QUERY_LENGTH:
            raise ValidationError(
                f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters"
            )

        # Validate n_results
        if n_results < 1:
            raise ValidationError("n_results must be at least 1")

        if n_results > MAX_N_RESULTS:
            logger.warning(f"n_results {n_results} exceeds maximum {MAX_N_RESULTS}, capping to maximum")
            n_results = MAX_N_RESULTS

        # Use cached search if enabled
        if self.enable_caching:
            cache_key = (sanitized_query, n_results)
            if cache_key in self._search_cache:
                logger.debug(f"Cache hit for query: {sanitized_query}")
                return self._search_cache[cache_key]

            results = self._cached_search(sanitized_query, n_results)

            # Implement simple LRU with max 128 entries
            if len(self._search_cache) >= 128:
                # Remove oldest entry (FIFO for simplicity)
                oldest_key = next(iter(self._search_cache))
                del self._search_cache[oldest_key]

            self._search_cache[cache_key] = results
            return results
        else:
            return self._cached_search(sanitized_query, n_results)
