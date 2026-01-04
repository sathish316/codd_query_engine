"""
Structured output models for PromQL query generation.
"""

from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class GenerationAttempt:
    """
    Represents a single query generation attempt.

    Attributes:
        attempt_number: The attempt number (1-indexed)
        query: The generated query for this attempt
        validation_result: The validation result (None if not yet validated)
        timestamp: When this attempt was made
        error: Error message if generation failed
    """

    attempt_number: int
    query: str
    validation_result: Optional[dict] = None  # Validation result as dict
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "attempt_number": self.attempt_number,
            "query": self.query,
            "validation_result": self.validation_result,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


@dataclass
class QueryGenerationContext:
    """
    Context for query generation that tracks attempts across iterations.

    Attributes:
        intent: The original query intent
        namespace: The namespace for validation
        attempts: List of all generation attempts
        max_attempts: Maximum number of attempts allowed
    """

    intent: "MetricsQueryIntent"
    namespace: str
    attempts: List[GenerationAttempt] = field(default_factory=list)
    max_attempts: int = 5

    def add_attempt(self, query: str, validation_result: Optional[dict] = None, error: Optional[str] = None) -> GenerationAttempt:
        """Add a new generation attempt."""
        attempt = GenerationAttempt(
            attempt_number=len(self.attempts) + 1,
            query=query,
            validation_result=validation_result,
            error=error,
        )
        self.attempts.append(attempt)
        return attempt

    def get_current_attempt_number(self) -> int:
        """Get the current attempt number (0 if no attempts yet)."""
        return len(self.attempts)

    def has_reached_max_attempts(self) -> bool:
        """Check if max attempts has been reached."""
        return len(self.attempts) >= self.max_attempts

    def get_attempt_history_summary(self) -> str:
        """Get a summary of previous attempts for context."""
        if not self.attempts:
            return "No previous attempts."

        summary_parts = []
        for attempt in self.attempts:
            status = "✓ Valid" if attempt.validation_result and attempt.validation_result.get("is_valid") else "✗ Invalid"
            summary_parts.append(
                f"Attempt {attempt.attempt_number}: {attempt.query} - {status}"
            )
            if attempt.validation_result and not attempt.validation_result.get("is_valid"):
                error = attempt.validation_result.get("error", "Unknown error")
                summary_parts.append(f"  Error: {error}")

        return "\n".join(summary_parts)


@dataclass
class QueryGenerationResult:
    """
    Result of query generation with ReAct pattern.

    Attributes:
        query: The final generated PromQL query
        success: Whether generation succeeded
        error: Optional error message if generation failed
        attempts: List of all generation attempts made
        total_attempts: Total number of attempts made
    """

    query: str
    success: bool
    error: Optional[str] = None
    attempts: List[GenerationAttempt] = field(default_factory=list)
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
