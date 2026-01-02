"""Configuration for semantic metadata store (ChromaDB)."""

from pydantic import BaseModel


class SemanticStoreConfig(BaseModel):
    """Configuration for the semantic metadata store (ChromaDB)."""

    chromadb_path: str
    collection_name: str = "metrics_semantic_metadata"
