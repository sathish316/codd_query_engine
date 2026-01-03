"""Metrics controller for semantic search and PromQL query generation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from maverick_lib.client import MaverickClient
from maverick_lib.config import MaverickConfig
from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent
from maverick_engine.validation_engine.metrics.structured_outputs import SearchResult

router = APIRouter()

# Initialize Maverick client (singleton)
_client: Optional[MaverickClient] = None


def get_client() -> MaverickClient:
    """Get or create Maverick client."""
    global _client
    if _client is None:
        config = MaverickConfig()
        _client = MaverickClient(config)
    return _client


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


class MetricsQueryResponse(BaseModel):
    """Response model for metrics query generation."""

    query: str
    success: bool
    error: Optional[str] = None


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
        client = get_client()
        results = client.metrics.search_relevant_metrics(
            request.query, limit=request.limit
        )
        return MetricsSearchResponse(results=results, count=len(results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/promql/generate", response_model=MetricsQueryResponse)
async def generate_promql_query(request: PromQLQueryRequest):
    """
    Generate a PromQL query from metrics query intent.

    Args:
        request: PromQL query intent with description, namespace, etc.

    Returns:
        Generated PromQL query

    Example:
        POST /api/metrics/promql/generate
        Body: {
          "description": "API error rate",
          "namespace": "production",
          "metric_name": "http_requests_total",
          "aggregation": "rate",
          "filters": {"status": "500"}
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
        )

        # Generate query
        client = get_client()
        result = await client.metrics.construct_promql_query(intent, request.namespace)

        return MetricsQueryResponse(
            query=result.query, success=result.success, error=result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
