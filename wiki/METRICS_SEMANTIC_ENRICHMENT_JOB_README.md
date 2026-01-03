# Metrics Semantic Indexer Job

Offline job for enriching and semantically indexing metrics metadata from Prometheus.

## Overview

This job performs the following steps:

1. **Fetch Metrics**: Queries metric metadata from Prometheus using the PromQL client
2. **Update Redis**: Stores metric names in Redis for fast exact-match validation
3. **Enrich with LLM**: Uses Claude Opus to enrich metrics with comprehensive semantic metadata
4. **Index Semantically**: Indexes enriched metadata into ChromaDB for semantic search

The job processes metrics in batches and provides real-time progress updates.

## Features

- **Batch Processing**: Processes metrics in configurable batches (default: 10)
- **Progress Tracking**: Real-time console output showing enrichment progress
- **Dual Storage**: Updates both Redis (exact match) and ChromaDB (semantic search)
- **LLM Enrichment**: Uses Claude Opus to generate rich semantic metadata
- **Error Handling**: Continues processing on individual metric failures
- **Statistics**: Provides detailed summary of job execution

## Prerequisites

- Prometheus server accessible via HTTP
- Redis server running
- ChromaDB server running
- Opus Agent Base configured with API credentials

## Installation

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python -m maverick_jobs.metrics_semantic_indexer_main \
    --namespace "production:order-service" \
    --promql-url "http://localhost:9090"
```

### Full Options

```bash
python -m maverick_jobs.metrics_semantic_indexer_main \
    --namespace "production:order-service" \
    --promql-url "http://localhost:9090" \
    --redis-host "localhost" \
    --redis-port 6380 \
    --redis-db 0 \
    --chromadb-host "localhost" \
    --chromadb-port 8000 \
    --batch-size 10 \
    --limit 100 \
    --log-level INFO
```

### Command Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--namespace` | Yes | - | Namespace for metrics (format: `tenant:service`) |
| `--promql-url` | No | `http://localhost:9090` | Prometheus base URL |
| `--redis-host` | No | `localhost` | Redis host |
| `--redis-port` | No | `6380` | Redis port |
| `--redis-db` | No | `0` | Redis database number |
| `--chromadb-host` | No | `localhost` | ChromaDB host |
| `--chromadb-port` | No | `8000` | ChromaDB port |
| `--batch-size` | No | `10` | Metrics per batch |
| `--limit` | No | None | Limit metrics to process (for testing) |
| `--log-level` | No | `INFO` | Logging level |

## Example Output

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
        ...

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

## Architecture

### Components

1. **MetricsEnrichmentAgent** (`maverick_engine/agent/metrics_enrichment_agent.py`)
   - LLM-based agent using Claude Opus
   - Enriches raw metrics with semantic metadata
   - Generates structured output with 11 metadata fields

2. **MetricsSemanticIndexerJob** (`maverick_jobs/metrics_semantic_indexer_job.py`)
   - Main job orchestrator
   - Manages batch processing and progress tracking
   - Coordinates between PromQL, Redis, and ChromaDB

3. **Main Entry Point** (`maverick_jobs/metrics_semantic_indexer_main.py`)
   - CLI interface
   - Initializes clients and managers
   - Handles error cases and logging

### Data Flow

```
┌──────────────┐
│  Prometheus  │
│   (PromQL)   │
└──────┬───────┘
       │
       │ Fetch Metadata
       ▼
┌──────────────────────────┐
│  MetricsSemanticIndexer  │
│         Job              │
└────┬─────────────────┬───┘
     │                 │
     │ Exact Match     │ LLM Enrichment
     ▼                 ▼
┌─────────┐      ┌──────────────────┐
│  Redis  │      │ MetricsEnrichment│
│  Store  │      │      Agent       │
└─────────┘      └────────┬─────────┘
                          │
                          │ Semantic Index
                          ▼
                    ┌──────────┐
                    │ ChromaDB │
                    │  Store   │
                    └──────────┘
```

### Enriched Metadata Fields

The LLM enriches each metric with:

- `metric_name`: Metric identifier
- `type`: Metric type (gauge, counter, histogram, timer)
- `description`: Natural language description
- `unit`: Unit of measurement
- `category`: High-level category (application, infrastructure, etc.)
- `subcategory`: Specific area (http, database, memory, etc.)
- `category_description`: Category explanation
- `golden_signal_type`: Monitoring signal (latency, traffic, errors, saturation)
- `golden_signal_description`: Observability context
- `meter_type`: Instrumentation type
- `meter_type_description`: Meter type explanation

## Logging

Logs are written to:
- **Console**: Real-time progress and status
- **File**: `metrics_semantic_indexer.log` (detailed logs)

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## Error Handling

The job implements robust error handling:

- **Connection Failures**: Validates Redis and ChromaDB connectivity before starting
- **Individual Metric Failures**: Logs and continues processing other metrics
- **Prometheus Errors**: Fails fast if Prometheus is unreachable
- **LLM Failures**: Catches enrichment errors and reports in summary

## Testing

### Test with Limited Metrics

```bash
python -m maverick_jobs.metrics_semantic_indexer_main \
    --namespace "test:sample-service" \
    --limit 10 \
    --log-level DEBUG
```

### Run Against Local Services

Ensure services are running:

```bash
# Start Redis
docker run -d -p 6380:6379 redis:latest

# Start ChromaDB
docker run -d -p 8000:8000 chromadb/chroma:latest

# Start Prometheus (with your config)
docker run -d -p 9090:9090 prom/prometheus
```

## Scheduling

For production use, schedule the job using:

- **Cron**: Run periodically
- **Kubernetes CronJob**: For containerized environments
- **APScheduler**: For Python-based scheduling

Example cron (daily at 2 AM):

```cron
0 2 * * * cd /path/to/maverickv2 && python -m maverick_jobs.metrics_semantic_indexer_main --namespace "production:my-service"
```

## Performance Considerations

- **Batch Size**: Larger batches reduce LLM API overhead but increase memory
- **Rate Limiting**: LLM calls may be rate-limited; adjust batch size accordingly
- **Concurrent Jobs**: Avoid running multiple jobs for same namespace simultaneously
- **Redis Memory**: Ensure sufficient memory for all metric names

## Troubleshooting

### Connection Errors

```
Failed to connect to Redis: [Errno 61] Connection refused
```

**Solution**: Ensure Redis is running and accessible:
```bash
redis-cli ping
```

### LLM Enrichment Failures

```
Failed to enrich metric: API rate limit exceeded
```

**Solution**:
- Reduce batch size
- Add delays between batches
- Check API quota and limits

### Prometheus Unreachable

```
Prometheus health check failed
```

**Solution**: Verify Prometheus URL and accessibility:
```bash
curl http://localhost:9090/-/healthy
```

## Related Components

- **PromQL Client**: `maverick_dal/metrics/promql_client.py`
- **Redis Metadata Store**: `maverick_dal/metrics/metrics_metadata_store.py`
- **Semantic Store**: `maverick_dal/metrics/metrics_semantic_metadata_store.py`
- **Query Intent**: `maverick_engine/querygen_engine/metrics/structured_inputs.py`

## License

See project LICENSE file.
