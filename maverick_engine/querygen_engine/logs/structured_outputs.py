from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, Field
from maverick_engine.querygen_engine.logs.models import LogQueryBackend


@dataclass(slots=True)
class LogQueryResult:
    """Generated query alongside basic metadata."""

    query: str
    backend: LogQueryBackend
    used_patterns: list[str] = field(default_factory=list)
    levels: list[str] = field(default_factory=list)
    selector: str | None = None


@dataclass
class QueryGenerationResult:
    """
    Result of query generation with ReAct pattern.

    Attributes:
        query: The final generated log query
        success: Whether generation succeeded
        error: Optional error message if generation failed
    """

    query: str
    success: bool
    error: Optional[str] = None


class QueryGenerationError(Exception):
    """Exception raised when query generation fails."""

    pass


class LogQLQueryResponse(BaseModel):
    """
    Response schema for LogQL query generation.

    Contains the generated LogQL query and reasoning about the generation.
    """

    query: str = Field(..., description="The generated LogQL query")
    reasoning: str = Field(
        ...,
        description="Explanation of why this query was generated and how it addresses the intent",
    )
