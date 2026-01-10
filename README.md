# Overview

Maverick is a Text2SQL Engine that can be used by AI Agents and Humans to query Databases (MySQL, Postgres, Neo4j etc) and Observability systems (Prometheus, Loki, Splunk etc)

# Architecture

<img src="MaverickArchitecture.drawio.png" alt="Maverick Architecture" width="100%">

# Installation

# Getting started

# Development

## Prerequisites

1. Install Redis

$ docker-compose up -d

1. Install ChromaDB or Qdrant

$ docker-compose up -d

## Build and Test

Run unit tests

```
uv run pytest -v

uv run pytest -v -s tests/unit/maverick_dal/metrics/test_metrics_metadata_store.py

uv run pytest -v -s tests/unit/maverick_dal/metrics/test_metrics_metadata_store.py::TestMetricsMetadataStore::test_is_valid_metric_name
```

Run integration tests

```
uv run pytest -m integration -v tests/integration
```

Note: Integration tests emit logs to Logfire with environment tags (integration, integration_querygen_evals). Set `LOGFIRE_TOKEN` environment variable to enable.

Run NL2SQL Evals
TODO

## Add Query Engine

# License

MIT License - see the [LICENSE](LICENSE) file for details

