# Overview

Maverick is a Text2SQL or NL2SQL Engine that can be leveraged by AIAgents and Humans to query databases, observability, analytics systems.

# Design

TODO: Diagram

* Maverick Service
* Maverick DAL (Data access layer)
* Maverick Engine
* LLM Engine

# Installation

# Getting started

# Development

## Prerequisites
1. Install Redis

$ docker-compose up -d

2. Install ChromaDB or Qdrant

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

Run NL2SQL Evals
TODO

## Add Query Engine

# License