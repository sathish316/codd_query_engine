"""
ChromaDB-based semantic metadata store for metrics.

This module provides semantic search capabilities for metrics metadata using vector embeddings.
Unlike the Redis-based exact-match store, this enables natural language queries to find
similar metrics based on descriptions, categories, and other metadata.
"""

import re
import logging
import chromadb

from maverick_engine.models.metrics_common import MetricMetadata
from maverick_engine.validation_engine.metrics.validation_result import ValidationError

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
METRIC_NAME_PATTERN = re.compile(r"^[\w._\-/]+$", re.UNICODE)


class MetricsSemanticMetadataStore:
    """
    Client for managing metrics metadata with semantic search capabilities.

    Provides methods to index and search metrics metadata using vector embeddings
    for natural language queries and semantic similarity.

    Args:
        chromadb_client: ChromaDB client instance
        collection_name: Name of the collection (default: "metrics_semantic_metadata")
    """

    def __init__(
        self,
        chromadb_client: chromadb.Client,
        collection_name: str = "metrics_semantic_metadata",
    ):
        """
        Initialize the metrics semantic metadata store.

        Args:
            chromadb_client: ChromaDB client instance for data operations
            collection_name: Name of the collection to use (default: "metrics_semantic_metadata")
        """
        self.chromadb_client = chromadb_client
        self.collection_name = collection_name

        try:
            # Get or create the collection with optimized settings
            self.collection = self.chromadb_client.get_or_create_collection(
                name=self.collection_name,
                # TODO: use config for vector store settings
                metadata={
                    "hnsw:space": "cosine",  # Cosine similarity for semantic search
                    "hnsw:construction_ef": 200,  # Higher quality index construction
                    "hnsw:search_ef": 100,  # Balance between speed and accuracy
                    "hnsw:M": 16,  # Number of connections per element
                },
            )
            logger.info(f"Initialized collection '{self.collection_name}'")
        except Exception as e:
            logger.error(
                f"Failed to initialize collection '{self.collection_name}': {e}"
            )
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
                "metric_name contains invalid characters. "
                "Only alphanumeric, dots, dashes, underscores, and slashes are allowed"
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
        sanitized = text.replace("\x00", "").strip()

        # Replace multiple whitespaces with single space
        sanitized = re.sub(r"\s+", " ", sanitized)

        return sanitized

    def index_metadata(self, namespace: str, metadata: MetricMetadata) -> str:
        """
        Index metric metadata for semantic search.

        Creates a searchable document by combining key metadata fields and stores
        all metadata for retrieval. Uses namespace x metric_name as document ID for upsert semantics
        (re-indexing the same metric updates existing document).

        Args:
            namespace: Namespace identifier
            metadata: Dictionary containing MetricMetadata with required field:

        Returns:
            Document ID (same as namespace x metric_name)

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
            "type",
            "description",
            "unit",
            "category",
            "subcategory",
            "category_description",
            "golden_signal_type",
            "golden_signal_description",
            "meter_type",
            "meter_type_description",
        ]

        # Validate all text fields
        for field_name in text_fields:
            field_value = metadata.get(field_name, "")
            if field_value:
                self._validate_text_field(field_name, str(field_value))

        try:
            # Create searchable document text by combining key fields
            # Use list comprehension for better performance
            document_parts = [
                self._sanitize_text(str(metadata.get(field, "")))
                for field in [
                    "description",
                    "category",
                    "subcategory",
                    "golden_signal_type",
                    "meter_type",
                ]
                if metadata.get(field)
            ]

            # Add labels for better semantic context
            labeled_parts = []
            field_labels = {
                "category": "Category",
                "subcategory": "Subcategory",
                "golden_signal_type": "Golden Signal",
                "meter_type": "Meter Type",
            }

            for field, label in field_labels.items():
                if metadata.get(field):
                    labeled_parts.append(
                        f"{label}: {self._sanitize_text(str(metadata[field]))}"
                    )

            # Combine description with labeled fields
            if metadata.get("description"):
                document_parts = [
                    self._sanitize_text(str(metadata["description"]))
                ] + labeled_parts
            else:
                document_parts = labeled_parts

            document_text = (
                " | ".join(document_parts) if document_parts else metric_name
            )

            # Extract all metadata fields for storage using dict comprehension
            metadata_dict = {
                field: self._sanitize_text(str(metadata.get(field, "")))
                for field in text_fields
            }
            metadata_dict["namespace"] = namespace

            # Upsert document to collection (updates if exists, adds if new)
            document_id = f"{namespace}#{metric_name}"
            self.collection.upsert(
                documents=[document_text], metadatas=[metadata_dict], ids=[document_id]
            )

            logger.debug(f"Indexed metric: {document_id}")
            return document_id

        except Exception as e:
            logger.error(f"Failed to index metric '{document_id}': {e}")
            raise

    def metric_exists(self, namespace: str, metric_name: str) -> bool:
        """
        Check if a metric already exists in the semantic store.

        Args:
            namespace: Namespace identifier
            metric_name: Metric name to check

        Returns:
            True if metric exists, False otherwise
        """
        try:
            document_id = f"{namespace}#{metric_name}"
            result = self.collection.get(ids=[document_id])
            return bool(result and result.get("ids") and len(result["ids"]) > 0)
        except Exception as e:
            logger.warning(f"Error checking if metric exists: {e}")
            return False

    def search_metadata(self, query: str, n_results: int = 10) -> list[dict]:
        """
        Search for metrics using semantic similarity.

        Performs vector similarity search to find metrics most relevant to the query.
        Results are ranked by semantic similarity. Supports LRU caching for repeated queries.

        Args:
            namespace: Namespace identifier
            query: Natural language search query
            n_results: Maximum number of results to return (default: 10, max: 100)

        Returns:
            List of dictionaries containing metric information and similarity scores.
            Each dictionary contains:
            - document_id (str): The document identifier (namespace x metric_name)
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
            logger.warning(
                f"n_results {n_results} exceeds maximum {MAX_N_RESULTS}, capping to maximum"
            )
            n_results = MAX_N_RESULTS

        results = self.collection.query(
            query_texts=[sanitized_query], n_results=n_results
        )

        # Format results
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        formatted_results = []
        ids = results["ids"][0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else 1.0

            # Extract metric_name from document_id (format: namespace#metric_name)
            metric_name = doc_id.split("#")[-1] if "#" in doc_id else doc_id

            result = {
                "metric_name": metric_name,
                "similarity_score": 1.0 - distance,  # Convert distance to similarity
                **metadata,
            }
            formatted_results.append(result)

        return formatted_results
