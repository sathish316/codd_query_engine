"""
ChromaDB-based semantic metadata store for metrics.

This module provides semantic search capabilities for metrics metadata using vector embeddings.
Unlike the Redis-based exact-match store, this enables natural language queries to find
similar metrics based on descriptions, categories, and other metadata.
"""

from typing import Optional
import chromadb


class MetricsSemanticMetadataStore:
    """
    Client for managing metrics metadata with semantic search capabilities using ChromaDB.

    Provides methods to index and search metrics metadata using vector embeddings
    for natural language queries and semantic similarity.

    Args:
        chromadb_client: ChromaDB client instance (supports in-memory, persistent, or client-server modes)
        collection_name: Name of the ChromaDB collection (default: "metrics_semantic_metadata")
    """

    def __init__(
        self,
        chromadb_client: chromadb.Client,
        collection_name: str = "metrics_semantic_metadata"
    ):
        """
        Initialize the metrics semantic metadata store.

        Args:
            chromadb_client: ChromaDB client instance for data operations
            collection_name: Name of the collection to use (default: "metrics_semantic_metadata")
        """
        self.chromadb_client = chromadb_client
        self.collection_name = collection_name

        # Get or create the collection (idempotent operation)
        self.collection = self.chromadb_client.get_or_create_collection(
            name=self.collection_name
        )

    def index_metadata(self, metadata: dict) -> str:
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
            KeyError: If metric_name is not provided in metadata
        """
        if "metric_name" not in metadata:
            raise KeyError("metric_name is required in metadata")

        metric_name = metadata["metric_name"]

        # Create searchable document text by combining key fields
        # These fields provide the richest semantic context for search
        document_parts = []

        if metadata.get("description"):
            document_parts.append(metadata["description"])
        if metadata.get("category"):
            document_parts.append(f"Category: {metadata['category']}")
        if metadata.get("subcategory"):
            document_parts.append(f"Subcategory: {metadata['subcategory']}")
        if metadata.get("golden_signal_type"):
            document_parts.append(f"Golden Signal: {metadata['golden_signal_type']}")
        if metadata.get("meter_type"):
            document_parts.append(f"Meter Type: {metadata['meter_type']}")

        document_text = " | ".join(document_parts) if document_parts else metric_name

        # Extract all metadata fields for storage
        metadata_dict = {
            "type": metadata.get("type", ""),
            "description": metadata.get("description", ""),
            "unit": metadata.get("unit", ""),
            "category": metadata.get("category", ""),
            "subcategory": metadata.get("subcategory", ""),
            "category_description": metadata.get("category_description", ""),
            "golden_signal_type": metadata.get("golden_signal_type", ""),
            "golden_signal_description": metadata.get("golden_signal_description", ""),
            "meter_type": metadata.get("meter_type", ""),
            "meter_type_description": metadata.get("meter_type_description", ""),
        }

        # Upsert document to collection (updates if exists, adds if new)
        self.collection.upsert(
            documents=[document_text],
            metadatas=[metadata_dict],
            ids=[metric_name]
        )

        return metric_name

    def search_metadata(self, query: str, n_results: int = 10) -> list[dict]:
        """
        Search for metrics using semantic similarity.

        Performs vector similarity search to find metrics most relevant to the query.
        Results are ranked by semantic similarity.

        Args:
            query: Natural language search query
            n_results: Maximum number of results to return (default: 10)

        Returns:
            List of dictionaries containing metric information and similarity scores.
            Each dictionary contains:
            - metric_name (str): The metric identifier
            - similarity_score (float): Similarity score between 0 and 1 (higher is more similar)
            - All metadata fields (type, description, unit, etc.)

        Note:
            Returns empty list if no metrics are indexed or query returns no results.
        """
        if not query or not query.strip():
            return []

        # Query the collection for similar documents
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # Parse and format results
        formatted_results = []

        if results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []

            for i, metric_name in enumerate(ids):
                result_dict = {
                    "metric_name": metric_name,
                    "similarity_score": 1 - distances[i] if distances else 0.0,
                }

                # Add all metadata fields
                if metadatas and i < len(metadatas):
                    result_dict.update(metadatas[i])

                formatted_results.append(result_dict)

        return formatted_results
