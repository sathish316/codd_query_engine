# Metrics Semantic Indexer - Architecture

## Overview

The Metrics Semantic Indexer is an offline batch job that enriches Prometheus metrics with comprehensive semantic metadata using LLM and indexes them for both exact-match and semantic search.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    METRICS SEMANTIC INDEXER JOB                      │
│                   (metrics_semantic_indexer_job.py)                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ Orchestrates
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌────────────────┐     ┌────────────────┐
│   PROMQL      │      │ METRICS        │     │   SEMANTIC     │
│   CLIENT      │      │ ENRICHMENT     │     │   STORE        │
│               │      │ AGENT (LLM)    │     │  (ChromaDB)    │
│ Query         │      │                │     │                │
│ Metadata      │      │ Enrich with    │     │ Vector         │
│ from          │      │ Claude Opus    │     │ Search         │
│ Prometheus    │      │                │     │                │
└───────┬───────┘      └────────┬───────┘     └────────┬───────┘
        │                       │                      │
        │                       │                      │
        ▼                       │                      │
┌───────────────┐               │                      │
│ REDIS STORE   │               │                      │
│               │◄──────────────┘                      │
│ Exact Match   │                                      │
│ Validation    │                                      │
└───────────────┘                                      │
                                                       │
                                            Semantic Search Results
                                                       │
                                                       ▼
                                            ┌──────────────────┐
                                            │  Users/Services  │
                                            │  Natural Lang    │
                                            │  Queries         │
                                            └──────────────────┘
```

## Component Details

### 1. Metrics Semantic Indexer Job
**File**: `codd_jobs/metrics_semantic_indexer_job.py`

**Responsibilities**:
- Orchestrate the entire indexing workflow
- Manage batch processing (default: 10 metrics per batch)
- Track statistics (total, processed, enriched, indexed, failed)
- Provide real-time progress updates to console
- Handle errors gracefully and continue processing

**Key Methods**:
- `run(namespace, limit)` - Main entry point
- `_fetch_metrics_from_prometheus(limit)` - Get raw metrics
- `_update_redis_store(namespace, metrics)` - Update exact-match store
- `_process_metrics_in_batches(namespace, metrics)` - Batch processor
- `_process_batch(...)` - Single batch handler with progress

### 2. Metrics Enrichment Agent
**File**: `codd_engine/agent/metrics_enrichment_agent.py`

**Responsibilities**:
- Use Claude Opus LLM to enrich metric metadata
- Generate 11 semantic fields from metric name, type, and help text
- Convert Pydantic output to MetricMetadata TypedDict
- Handle enrichment errors

**Input**:
- `metric_name`: e.g., "http_request_duration_seconds"
- `metric_type`: e.g., "histogram"
- `description`: e.g., "HTTP request duration in seconds"

**Output** (EnrichedMetricMetadata):
```python
{
    "metric_name": "http_request_duration_seconds",
    "type": "histogram",
    "description": "Histogram measuring HTTP request duration...",
    "unit": "seconds",
    "category": "application",
    "subcategory": "http",
    "category_description": "Application-level HTTP metrics",
    "golden_signal_type": "latency",
    "golden_signal_description": "Measures request latency...",
    "meter_type": "histogram",
    "meter_type_description": "Histogram captures distribution..."
}
```

**Key Methods**:
- `enrich_metric(metric_name, metric_type, description)` - Returns Pydantic model
- `enrich_metric_to_dict(...)` - Returns MetricMetadata dict
- `_format_enrichment_prompt(...)` - Create LLM prompt
- `_execute_enrichment(prompt)` - Call LLM agent

### 3. PromQL Client
**File**: `codd_dal/metrics/promql_client.py`

**Responsibilities**:
- Query Prometheus HTTP API
- Fetch metric metadata (names, types, help text)
- Health checks and validation

**Key Methods**:
- `get_metric_metadata(metric, limit)` - Fetch metadata
- `health_check()` - Verify Prometheus availability

### 4. Redis Metadata Store
**File**: `codd_dal/metrics/metrics_metadata_store.py`

**Responsibilities**:
- Store metric names in Redis sets for O(1) exact-match validation
- Namespace isolation: `<namespace>#metric_names`
- Fast schema validation during query generation

**Key Methods**:
- `set_metric_names(namespace, metric_names)` - Replace all metrics
- `get_metric_names(namespace)` - Retrieve metrics
- `is_valid_metric_name(namespace, metric_name)` - O(1) validation

**Data Model**:
```
Redis Key: "production:order-service#metric_names"
Redis Type: SET
Members: ["http_request_duration_seconds", "http_requests_total", ...]
```

### 5. Semantic Metadata Store (ChromaDB)
**File**: `codd_dal/metrics/metrics_semantic_metadata_store.py`

**Responsibilities**:
- Index enriched metadata for semantic search
- Enable natural language metric discovery
- Store 11 metadata fields per metric
- Vector similarity search using embeddings

**Key Methods**:
- `index_metadata(namespace, metadata)` - Index/upsert metric
- `search_metadata(query, n_results)` - Semantic search

**Data Model**:
```
Document ID: "<namespace>#<metric_name>"
Document Text: Concatenation of description + category + subcategory + golden_signal_type + meter_type
Metadata: All 11 fields stored as ChromaDB metadata
Vector: Embedding generated from document text
```

**Search Example**:
```python
results = store.search_metadata("p99 latency for HTTP requests", n_results=5)
# Returns metrics ranked by semantic similarity
```

### 6. Main Entry Point
**File**: `codd_jobs/metrics_semantic_indexer_main.py`

**Responsibilities**:
- CLI interface with argument parsing
- Initialize Redis and ChromaDB clients
- Initialize LLM agent managers
- Handle errors and logging
- Provide exit codes

**Usage**:
```bash
python -m codd_jobs.metrics_semantic_indexer_main \
    --namespace "production:order-service" \
    --promql-url "http://localhost:9090" \
    --batch-size 10 \
    --limit 100
```

## Execution Flow

```
START
  │
  ├─► Parse CLI Arguments
  │
  ├─► Initialize Clients
  │   ├─► Redis Client (test connection with ping)
  │   ├─► ChromaDB Client (test connection with heartbeat)
  │   └─► ConfigManager & InstructionsManager
  │
  ├─► Create MetricsSemanticIndexerJob
  │
  ├─► Run Job
  │   │
  │   ├─► [1/4] Fetch Metrics from Prometheus
  │   │   ├─► Health check
  │   │   ├─► Call get_metric_metadata()
  │   │   └─► Apply limit if specified
  │   │
  │   ├─► [2/4] Update Redis Store
  │   │   └─► set_metric_names(namespace, {metric1, metric2, ...})
  │   │
  │   ├─► [3/4] Process Metrics in Batches
  │   │   │
  │   │   └─► For each batch of 10 metrics:
  │   │       │
  │   │       └─► For each metric:
  │   │           ├─► Print: "→ Enriching: <metric_name>"
  │   │           ├─► Call enrichment_agent.enrich_metric_to_dict()
  │   │           │   ├─► Format LLM prompt
  │   │           │   ├─► Call Claude Opus
  │   │           │   └─► Parse structured output
  │   │           ├─► Call semantic_store.index_metadata()
  │   │           └─► Print: "✓ (category: X, signal: Y)"
  │   │
  │   └─► [4/4] Print Summary
  │       ├─► Total Metrics
  │       ├─► Processed
  │       ├─► Enriched (LLM)
  │       ├─► Indexed (Semantic)
  │       ├─► Failed
  │       └─► Success Rate
  │
  └─► EXIT (0=success, 1=error, 130=interrupted)
```

## Batch Processing Detail

```
Total Metrics: 50
Batch Size: 10
Number of Batches: 5

Batch 1 (metrics 1-10)
  ├─► Metric 1: Enrich → Index → Print ✓
  ├─► Metric 2: Enrich → Index → Print ✓
  ├─► Metric 3: Enrich → Index → Print ✓
  ...
  └─► Metric 10: Enrich → Index → Print ✓

Batch 2 (metrics 11-20)
  ├─► Metric 11: Enrich → Index → Print ✓
  ...

[Progress updates shown in real-time on console]

Batch 5 (metrics 41-50)
  └─► Metric 50: Enrich → Index → Print ✓

Final Summary Displayed
```

## Progress Output Format

```
======================================================================
METRICS SEMANTIC INDEXER JOB
======================================================================
Namespace: production:order-service
Batch Size: 10
Limit: 50
======================================================================

[1/4] Fetching metrics from Prometheus...
      ✓ Found 50 metrics

[2/4] Updating Redis metadata store...
      ✓ Redis updated with 50 metric names

[3/4] Enriching metrics using LLM and indexing to semantic store...
      Processing 50 metrics in 5 batches...

      Batch 1/5 (10 metrics):
        → Enriching: http_request_duration_seconds ✓ (category: application, signal: latency)
        → Enriching: http_requests_total ✓ (category: application, signal: traffic)
        → Enriching: http_requests_failed_total ✓ (category: application, signal: errors)
        → Enriching: process_resident_memory_bytes ✓ (category: infrastructure, signal: saturation)
        → Enriching: db_connection_pool_active ✓ (category: infrastructure, signal: saturation)
        → Enriching: cache_hit_rate ✓ (category: application, signal: none)
        → Enriching: cpu_usage_percent ✓ (category: infrastructure, signal: saturation)
        → Enriching: disk_io_bytes_total ✓ (category: infrastructure, signal: traffic)
        → Enriching: api_response_time_p99 ✓ (category: application, signal: latency)
        → Enriching: queue_depth ✓ (category: infrastructure, signal: saturation)

      Batch 2/5 (10 metrics):
        ...

[4/4] Indexing complete!

======================================================================
INDEXING SUMMARY
======================================================================
Total Metrics:      50
Processed:          50
Enriched (LLM):     48
Indexed (Semantic): 48
Failed:             2
Skipped:            0
======================================================================
Success Rate:       96.0%
======================================================================
```

## Error Handling

### Connection Errors
- Redis connection failure → Exit immediately
- ChromaDB connection failure → Exit immediately
- Prometheus connection failure → Exit immediately

### Individual Metric Errors
- LLM enrichment failure → Log warning, increment failed count, continue
- Indexing failure → Log error, increment failed count, continue
- Invalid metric data → Skip, increment skipped count, continue

### Graceful Degradation
- Job continues processing even if individual metrics fail
- Summary shows success/failure breakdown
- Logs detailed errors for debugging

## Configuration

### LLM Agent Configuration
**Prompt File**: `~/.codd/prompts/agent/metrics/METRICS_ENRICHMENT_AGENT_INSTRUCTIONS.md`

**Agent Settings** (via OpusAgentBase):
- Model: Claude Opus 4.5
- Output Type: Structured (EnrichedMetricMetadata Pydantic model)
- System Prompt: Loaded from instruction file

### Storage Configuration
**Redis**:
- Key pattern: `<namespace>#metric_names`
- Data type: SET (for O(1) lookups)

**ChromaDB**:
- Collection: `metrics_semantic_metadata`
- Distance metric: Cosine similarity
- HNSW parameters: `construction_ef=200`, `search_ef=100`, `M=16`

## Integration with Query Generation

After indexing, the semantic store enables:

1. **Schema Validation**: Redis provides O(1) metric name validation
2. **Semantic Discovery**: Users can find metrics using natural language
3. **Query Intent Enrichment**: Preprocessors use metadata for suggestions
4. **Semantic Validation**: Query explainer validates generated queries

Example:
```
User Query: "Show me p99 latency for HTTP endpoints"
  │
  ├─► Semantic Search: "p99 latency HTTP"
  │   └─► Returns: http_request_duration_seconds (category: application, signal: latency)
  │
  ├─► Create MetricsQueryIntent with metric: "http_request_duration_seconds"
  │
  ├─► Preprocessor adds aggregation suggestions based on meter_type: "histogram"
  │   └─► Suggests: histogram_quantile(0.99, ...)
  │
  ├─► Generate PromQL query
  │
  └─► Semantic validation ensures query matches intent
```

## Performance Considerations

### Batch Size
- **Smaller batches (5-10)**: Lower memory, easier to track, more API calls
- **Larger batches (20-50)**: Fewer API calls, higher memory, harder to track

### LLM Rate Limits
- Each metric requires 1 LLM API call
- Consider rate limits when setting batch size
- Add delays between batches if hitting limits

### Storage Performance
- **Redis**: O(1) set operations, very fast
- **ChromaDB**: Vector indexing takes time, scales with corpus size

### Recommended Settings
- **Development**: batch_size=5, limit=20
- **Production**: batch_size=10, limit=None (all metrics)
- **Large deployments**: Run during off-hours, monitor API quotas

## Monitoring and Observability

### Logs
- **Console**: Real-time progress and status
- **File**: `metrics_semantic_indexer.log` with detailed debug info

### Metrics to Track
- Total metrics indexed
- Success/failure rate
- Enrichment time per metric
- Indexing time per batch
- Error types and frequencies

### Alerting
- Job completion status
- High failure rate (>10%)
- Long execution time
- API rate limit errors

## Future Enhancements

1. **Incremental Updates**: Only index new/changed metrics
2. **Parallel Processing**: Process batches in parallel with worker pool
3. **Caching**: Cache LLM responses to avoid re-enriching
4. **Metrics Cleanup**: Remove stale metrics from stores
5. **Multi-namespace Support**: Index multiple namespaces in single run
6. **Progress Persistence**: Resume from checkpoint on failure
7. **Dry Run Mode**: Preview changes without indexing
8. **Validation**: Verify enriched data quality before indexing
