# Implementation Plan: ChromaDB-based Metrics Semantic Metadata Store
Task ID: coddv2-7vw

## Feature Overview and Goals

Implement a ChromaDB-based semantic store for metrics metadata that enables natural language search and semantic querying of metrics. Unlike the Redis-based store (which provides fast exact-match lookups), this semantic store uses vector embeddings to find similar metrics based on descriptions, categories, and metadata.

**Goals:**
- Enable semantic search for metrics using natural language queries
- Store rich metadata including categories, golden signals, and meter types
- Support vector similarity search for finding related metrics
- Complement the existing Redis-based exact-match store

## Component Breakdown

1. **MetricsSemanticMetadataStore class** (depends on: none)
   - Main client class in `codd-dal/metrics/metrics_semantic_metadata_store.py`
   - Accepts ChromaDB client via constructor injection
   - Manages `metrics_semantic_metadata` collection

2. **Schema and metadata model** (depends on: MetricsSemanticMetadataStore)
   - Document schema with 11 fields: metric_name, type, description, unit, category, subcategory, category_description, golden_signal_type, golden_signal_description, meter_type, meter_type_description
   - Metadata fields stored as ChromaDB metadata
   - Document text combines key searchable fields for embedding

3. **Core API methods** (depends on: Schema and metadata model)
   - `index_metadata(metadata: dict) -> str`: Index single metric metadata, returns document ID
   - `search_metadata(query: str, n_results: int = 10) -> list[dict]`: Semantic search, returns ranked results

4. **Unit tests** (depends on: Core API methods)
   - Test file at `codd-dal/metrics/tests/test_metrics_semantic_metadata_store.py`
   - Use in-memory ChromaDB client for testing

## Implementation Steps

1. **Create MetricsSemanticMetadataStore class**
   - Add imports: `import chromadb`, typing imports
   - Constructor accepts `chromadb.Client` and optional collection name
   - Initialize or get collection `metrics_semantic_metadata` in constructor
   - Store collection as instance variable

2. **Implement index_metadata method**
   - Accept metadata dict with required field: `metric_name`
   - Create searchable document text by combining: description, category, subcategory, golden_signal_type, meter_type
   - Extract metadata dict (all 11 schema fields)
   - Use `collection.add()` with document text, metadata, and metric_name as ID
   - Return document ID (metric_name)

3. **Implement search_metadata method**
   - Accept query string and optional n_results parameter (default 10)
   - Use `collection.query()` with query text and n_results
   - Parse results to extract documents, metadata, and distances
   - Return list of dicts containing: metric_name, metadata fields, similarity_score (1 - distance)

4. **Create unit tests**
   - Use `chromadb.Client()` in-memory client for testing
   - Test indexing single and multiple metrics
   - Test semantic search with various queries
   - Test edge cases: empty query, no results, missing fields
   - Test that similar metrics are retrieved by semantic search

## Acceptance Criteria

- MetricsSemanticMetadataStore class implemented in `codd-dal/metrics/metrics_semantic_metadata_store.py`
- `index_metadata(metadata)` stores metric metadata and returns document ID
- `search_metadata(query, n_results)` returns semantically similar metrics ranked by relevance
- Schema supports all 11 required fields: metric_name, type, description, unit, category, subcategory, category_description, golden_signal_type, golden_signal_description, meter_type, meter_type_description
- Collection name is `metrics_semantic_metadata`
- Unit tests pass with at least 85% coverage
- Type hints provided for all public methods

## Technical Considerations

- **ChromaDB client**: Accept `chromadb.Client` via constructor for flexibility (supports in-memory, persistent, and client-server modes)
- **Embedding function**: Use ChromaDB's default embedding function (sentence transformers) unless custom embeddings needed
- **Document text composition**: Combine description, category, subcategory, golden_signal_type, meter_type fields for rich semantic representation
- **ID strategy**: Use metric_name as document ID for upsert semantics (re-indexing same metric updates existing document)
- **Performance**: Semantic search is slower than Redis exact-match but provides discovery capabilities
- **Complementary design**: This store works alongside MetricsMetadataClient (Redis) - Redis for validation, ChromaDB for discovery
- **Edge cases**:
  - Missing optional fields should be handled gracefully (use empty string or None)
  - metric_name is required and must be unique per document
  - Empty queries should return most relevant documents or empty list
  - Collection initialization is idempotent (get_or_create semantics)
