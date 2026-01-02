"""Configuration for semantic metadata store (ChromaDB)."""

from typing import Optional

from pydantic import BaseModel


class SemanticStoreConfig(BaseModel):
    """Configuration for the semantic metadata store (ChromaDB)."""

    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    chromadb_path: Optional[str] = None
    collection_name: str = "metrics_semantic_metadata"
