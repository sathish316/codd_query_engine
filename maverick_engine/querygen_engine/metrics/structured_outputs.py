"""
Structured output models for PromQL query generation.
"""

from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryGenerationResult:
    """
    Result of query generation with ReAct pattern.

    Attributes:
        query: The final generated PromQL query
        success: Whether generation succeeded
        error: Optional error message if generation failed
    """

    query: str
    success: bool
    error: Optional[str] = None


class QueryGenerationError(Exception):
    """Exception raised when query generation fails."""

    pass


class PromQLQueryResponse(BaseModel):
    """
    Response schema for PromQL query generation.

    Contains the generated PromQL query and reasoning about the generation.
    """

    query: str = Field(..., description="The generated PromQL query")
    reasoning: str = Field(
        ...,
        description="Explanation of why this query was generated and how it addresses the intent",
    )
