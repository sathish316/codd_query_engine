"""Pydantic models for log queries."""

from pydantic import BaseModel, Field
from typing import Optional


class LogPattern(BaseModel):
    """Pydantic model for log pattern."""

    pattern: str = Field(..., description="Pattern to search for")
    level: Optional[str] = Field(None, description="Log level for this pattern")


class LogQueryIntent(BaseModel):
    """Pydantic model for LogQL/Splunk query generation intent.

    This model is used by both the REST API and MCP server for type-safe
    request handling.
    """

    description: str = Field(..., description="What logs to search for")
    service: str = Field(..., description="Service name")
    patterns: list[LogPattern] = Field(
        ..., description="List of patterns to search for"
    )
    namespace: str = Field(..., description="Codd Text2SQL namespace")
    default_level: Optional[str] = Field(None, description="Default log level")
    limit: int = Field(200, description="Maximum results to return")
