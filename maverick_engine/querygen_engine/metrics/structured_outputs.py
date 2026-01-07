"""
Structured output models for PromQL query generation.
"""

from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Optional, List


class QueryGenerationInput(BaseModel):
    """
    Input context for query generation with validation history.

    Tracks namespace, intent, and validation results across iterations.
    Attempts are inferred from len(validation_results).
    """

    namespace: str
    intent: "MetricsQueryIntent"
    validation_results: List[str] = Field(default_factory=list)
    max_attempts: int = 5

    def add_validation_result(self, error_message: str) -> None:
        """
        Add a validation error to the history.

        Args:
            error_message: The validation error message
        """
        if len(self.validation_results) < self.max_attempts:
            self.validation_results.append(error_message)

    def get_attempt_count(self) -> int:
        """Get the current attempt count."""
        return len(self.validation_results)

    def has_reached_max_attempts(self) -> bool:
        """Check if max attempts reached."""
        return len(self.validation_results) >= self.max_attempts

    def get_validation_history(self) -> str:
        """Get formatted validation history for prompt context."""
        if not self.validation_results:
            return ""

        history = ["**Previous Validation Errors:**"]
        for i, error in enumerate(self.validation_results, 1):
            history.append(f"Attempt {i}: {error}")
        return "\n".join(history)


@dataclass
class QueryGenerationResult:
    """
    Result of query generation with ReAct pattern.

    Attributes:
        query: The final generated PromQL query
        success: Whether generation succeeded
        error: Optional error message if generation failed
        total_attempts: Total number of attempts made
    """

    query: str
    success: bool
    error: Optional[str] = None
    total_attempts: int = 0


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
