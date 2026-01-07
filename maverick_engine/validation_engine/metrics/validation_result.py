"""
Base validation result class for all validation types.

This module provides the base ValidationResult class that all specific validation
results (SyntaxValidationResult, SchemaValidationResult, SemanticValidationResult)
should extend.
"""

from pydantic import BaseModel
from typing import List


class ValidationResult(BaseModel):
    """
    Base validation result for all validation types.

    All specific validation results (SyntaxValidationResult, SchemaValidationResult,
    SemanticValidationResult) should extend this class and add their own specific fields.

    Attributes:
        is_valid: True if validation passed, False otherwise
        error: Optional error message if validation failed
    """

    is_valid: bool
    error: str | None = None


class ValidationResultList(BaseModel):
    """
    Collection of multiple validation results with same interface as ValidationResult.

    Aggregates results from multiple validation stages (syntax, schema, semantics)
    and provides a unified interface matching singular ValidationResult.

    Attributes:
        is_valid: True only if ALL validation results are valid
        error: Combined formatted error message from all failed validations
        results: List of individual validation results
    """

    results: List[ValidationResult]

    @property
    def is_valid(self) -> bool:
        """Check if all validation results are valid."""
        return all(result.is_valid for result in self.results)

    @property
    def error(self) -> str | None:
        """Get formatted error message combining all validation errors."""
        if self.is_valid:
            return None

        error_parts = []
        for result in self.results:
            if result.error:
                # Determine validation stage from result type
                stage = result.__class__.__name__.replace("ValidationResult", "")
                error_parts.append(f"**{stage.upper()} ERROR:** {result.error}")

        return "\n\n".join(error_parts) if error_parts else None


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass
