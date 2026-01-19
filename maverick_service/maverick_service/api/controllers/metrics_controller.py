"""Metrics controller for semantic search and PromQL query generation."""

import logging
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

from maverick_lib.client import MaverickClient
from maverick_lib.config import MaverickConfig
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.validation_engine.metrics.structured_outputs import SearchResult

router = APIRouter()

# Global config and client
_config: Optional[MaverickConfig] = None
_client: Optional[MaverickClient] = None


def get_client(shared: bool = False) -> MaverickClient:
    """Get or create Maverick client.

    Args:
        shared: If True, use the global singleton client. If False, create a new client for every request.
    """
    global _config, _client

    if _config is None:
        _config = MaverickConfig.from_config_file()

    if shared:
        if _client is None:
            _client = MaverickClient(_config)
        return _client
    else:
        return MaverickClient(_config)


class MetricsSearchRequest(BaseModel):
    """Request model for semantic metrics search."""

    query: str
    limit: int = 5


class MetricsSearchResponse(BaseModel):
    """Response model for semantic metrics search."""

    results: list[SearchResult]
    count: int


class PromQLQueryRequest(BaseModel):
    """Request model for PromQL query generation."""

    description: str
    namespace: str
    metric_name: Optional[str] = None
    aggregation: Optional[str] = None
    group_by: Optional[list[str]] = None
    filters: Optional[dict[str, str]] = None
    window: Optional[str] = None


class MetricsQueryResponse(BaseModel):
    """Response model for metrics query generation."""

    query: Optional[str]
    success: bool
    error: Optional[str] = None


class MetricExistsRequest(BaseModel):
    """Request model for checking if a metric exists."""

    namespace: str
    metric_name: str


class MetricExistsResponse(BaseModel):
    """Response model for metric existence check."""

    exists: bool
    namespace: str
    metric_name: str


class NamespaceMetricsRequest(BaseModel):
    """Request model for getting all metrics in a namespace."""

    namespace: str


class NamespaceMetricsResponse(BaseModel):
    """Response model for namespace metrics."""

    namespace: str
    metrics: list[str]
    count: int


@router.post("/search", response_model=MetricsSearchResponse)
async def search_metrics(request: MetricsSearchRequest):
    """
    Search for relevant metrics using semantic search.

    Args:
        request: Search query and limit

    Returns:
        List of relevant metrics with similarity scores

    Example:
        POST /api/metrics/search
        Body: {"query": "API high latency", "limit": 5}
    """
    try:
        client = get_client(True)
        results = client.metrics.search_relevant_metrics(
            request.query, limit=request.limit
        )
        return MetricsSearchResponse(results=results, count=len(results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/promql/generate", response_model=MetricsQueryResponse)
async def generate_promql_query(
    request: PromQLQueryRequest,
    x_cache_bypass: Optional[str] = Header(None, alias="X-Cache-Bypass"),
):
    """
    Generate a PromQL query from metrics query intent.

    Args:
        request: PromQL query intent with description, namespace, etc.
        x_cache_bypass: Header to bypass cache (set to "true" to skip cache lookup)

    Returns:
        Generated PromQL query

    Example:
        POST /api/metrics/promql/generate
        Headers: X-Cache-Bypass: true (optional, to bypass cache)
        Body: {
          "description": "API error rate",
          "namespace": "production",
          "metric_name": "http_requests_total",
          "aggregation": "rate",
          "filters": {"status": "500"},
          "window": "5m"
        }
    """
    try:
        # Create intent
        intent = MetricsQueryIntent(
            metric=request.metric_name or "",
            intent_description=request.description,
            metric_type=request.aggregation or "gauge",
            group_by=request.group_by or [],
            filters=request.filters or {},
            window=request.window or "5m",
            service_label=_config.prometheus.service_label,
        )

        logger.info(
            "Generating PromQL query for intent: metric=%s, description=%s, metric_type=%s, group_by=%s, filters=%s, window=%s, namespace=%s",
            intent.metric,
            intent.intent_description,
            intent.metric_type,
            intent.group_by,
            intent.filters,
            intent.window,
            request.namespace,
        )

        # Generate query (cache bypass is handled internally by client)
        bypass_cache = x_cache_bypass and x_cache_bypass.lower() == "true"
        client = get_client(False)
        result = await client.metrics.construct_promql_query(
            intent, request.namespace, bypass_cache=bypass_cache
        )

        logger.info(
            "Generated PromQL query: query=%s, success=%s, error=%s",
            result.query,
            result.success,
            result.error,
        )

        return MetricsQueryResponse(
            query=result.query,
            success=result.success,
            error=result.error,
        )
    except Exception as e:
        logger.exception("Failed to generate PromQL query: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exists", response_model=MetricExistsResponse)
async def check_metric_exists(request: MetricExistsRequest):
    """
    Check if a metric name exists in a namespace.

    Args:
        request: Namespace and metric name to check

    Returns:
        Boolean indicating if metric exists in the namespace

    Example:
        POST /api/metrics/exists
        Body: {
          "namespace": "production",
          "metric_name": "http_requests_total"
        }
    """
    try:
        client = get_client(True)
        exists = client.metrics.metric_exists(request.namespace, request.metric_name)
        return MetricExistsResponse(
            exists=exists, namespace=request.namespace, metric_name=request.metric_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/all", response_model=NamespaceMetricsResponse)
async def get_namespace_metrics(request: NamespaceMetricsRequest):
    """
    Get all metric names in a namespace.

    Args:
        request: Namespace identifier

    Returns:
        List of all metric names in the namespace

    Example:
        POST /api/metrics/namespace/metrics
        Body: {
          "namespace": "production"
        }
    """
    try:
        client = get_client(True)
        metrics = client.metrics.get_all_metrics(request.namespace)
        return NamespaceMetricsResponse(
            namespace=request.namespace, metrics=metrics, count=len(metrics)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
