"""Logs controller for LogQL and Splunk query generation."""

import logging
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from codd_lib.client import CoddClient
from codd_lib.config import CoddConfig
from codd_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from codd_engine.logs.log_patterns import LogPattern

logger = logging.getLogger(__name__)

router = APIRouter()

# Global config and client
_config: Optional[CoddConfig] = None
_client: Optional[CoddClient] = None


def get_client(shared: bool = False) -> CoddClient:
    """Get or create Codd client.

    Args:
        shared: If True, use the global singleton client. If False, create a new client for every request.
    """
    global _config, _client

    if _config is None:
        _config = CoddConfig.from_config_file()

    if shared:
        if _client is None:
            _client = CoddClient(_config)
        return _client
    else:
        return CoddClient(_config)


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
async def generate_logql_query(
    request: LogQLQueryRequest,
    x_cache_bypass: Optional[str] = Header(None, alias="X-Cache-Bypass"),
):
    """
    Generate a LogQL query for Loki.

    Args:
        request: LogQL query intent with description, service, patterns
        x_cache_bypass: Header to bypass cache (set to "true" to skip cache lookup)

    Returns:
        Generated LogQL query

    Example:
        POST /api/logs/logql/generate
        Headers: X-Cache-Bypass: true (optional, to bypass cache)
        Body: {
          "description": "Find error logs",
          "service": "payments",
          "patterns": [{"pattern": "error", "level": "error"}],
          "limit": 200
        }
    """
    try:
        # Get client (this also initializes _config)
        bypass_cache = x_cache_bypass and x_cache_bypass.lower() == "true"
        client = get_client(False)

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
            service_label=_config.loki.service_label,
            patterns=log_patterns,
            namespace=request.namespace,
            default_level=request.default_level or "error",
            limit=request.limit,
        )
        result = await client.logs.logql.construct_logql_query(intent, bypass_cache=bypass_cache)

        logger.info(
            "Generated LogQL query: query=%s, success=%s, error=%s",
            result.query,
            result.success,
            result.error,
        )

        return LogsQueryResponse(
            query=result.query,
            backend="loki",
            success=result.success,
            error=result.error,
        )
    except Exception as e:
        logger.exception("Failed to generate LogQL query: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/splunk/generate", response_model=LogsQueryResponse)
async def generate_splunk_query(
    request: SplunkQueryRequest,
    x_cache_bypass: Optional[str] = Header(None, alias="X-Cache-Bypass"),
):
    """
    Generate a Splunk SPL query.

    Args:
        request: Splunk query intent with description, service, patterns
        x_cache_bypass: Header to bypass cache (set to "true" to skip cache lookup)

    Returns:
        Generated Splunk SPL query

    Example:
        POST /api/logs/splunk/generate
        Headers: X-Cache-Bypass: true (optional, to bypass cache)
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

        # Generate query (cache bypass is handled internally by client)
        bypass_cache = x_cache_bypass and x_cache_bypass.lower() == "true"
        client = get_client(False)
        result = await client.logs.splunk.construct_spl_query(intent, bypass_cache=bypass_cache)

        logger.info(
            "Generated Splunk query: query=%s, success=%s, error=%s",
            result.query,
            result.success,
            result.error,
        )

        return LogsQueryResponse(
            query=result.query,
            backend="splunk",
            success=result.success,
            error=result.error,
        )
    except Exception as e:
        logger.exception("Failed to generate Splunk query: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
