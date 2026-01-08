"""Logs controller for LogQL and Splunk query generation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from maverick_lib.client import MaverickClient
from maverick_lib.config import MaverickConfig
from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.logs.log_patterns import LogPattern

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


class LogPatternRequest(BaseModel):
    """Request model for log pattern."""

    pattern: str
    level: Optional[str] = None


class LogQLQueryRequest(BaseModel):
    """Request model for LogQL query generation."""

    description: str
    service: str
    patterns: list[LogPatternRequest]
    namespace: Optional[str] = None
    default_level: Optional[str] = None
    limit: int = 200


class SplunkQueryRequest(BaseModel):
    """Request model for Splunk query generation."""

    description: str
    service: str
    patterns: list[LogPatternRequest]
    default_level: Optional[str] = None
    limit: int = 200


class LogsQueryResponse(BaseModel):
    """Response model for logs query generation."""

    query: Optional[str]
    backend: str
    success: bool
    error: Optional[str] = None


@router.post("/logql/generate", response_model=LogsQueryResponse)
async def generate_logql_query(request: LogQLQueryRequest):
    """
    Generate a LogQL query for Loki.

    Args:
        request: LogQL query intent with description, service, patterns

    Returns:
        Generated LogQL query

    Example:
        POST /api/logs/logql/generate
        Body: {
          "description": "Find error logs",
          "service": "payments",
          "patterns": [{"pattern": "error", "level": "error"}],
          "limit": 200
        }
    """
    try:
        # Convert request patterns to LogPattern dataclass instances
        log_patterns = [
            LogPattern(pattern=p.pattern, level=p.level or "info")
            for p in request.patterns
        ]

        # Create intent
        intent = LogQueryIntent(
            description=request.description,
            backend="loki",
            service=request.service,
            patterns=log_patterns,
            namespace=request.namespace,
            default_level=request.default_level or "error",
            limit=request.limit,
        )

        # Generate query
        client = get_client()
        result = await client.logs.logql.construct_logql_query(intent)

        return LogsQueryResponse(
            query=result.query,
            backend="loki",
            success=result.success,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/splunk/generate", response_model=LogsQueryResponse)
async def generate_splunk_query(request: SplunkQueryRequest):
    """
    Generate a Splunk SPL query.

    Args:
        request: Splunk query intent with description, service, patterns

    Returns:
        Generated Splunk SPL query

    Example:
        POST /api/logs/splunk/generate
        Body: {
          "description": "Search for timeouts",
          "service": "api-gateway",
          "patterns": [{"pattern": "timeout"}],
          "limit": 200
        }
    """
    try:
        # Convert request patterns to LogPattern dataclass instances
        log_patterns = [
            LogPattern(pattern=p.pattern, level=p.level or "info")
            for p in request.patterns
        ]

        # Create intent
        intent = LogQueryIntent(
            description=request.description,
            backend="splunk",
            service=request.service,
            patterns=log_patterns,
            default_level=request.default_level or "error",
            limit=request.limit,
        )

        # Generate query
        client = get_client()
        result = await client.logs.splunk.construct_spl_query(intent)

        return LogsQueryResponse(
            query=result.query,
            backend="splunk",
            success=result.success,
            error=result.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
