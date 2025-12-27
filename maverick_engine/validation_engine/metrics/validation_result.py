"""
Base validation result class for all validation types.

This module provides the base ValidationResult class that all specific validation
results (SyntaxValidationResult, SchemaValidationResult, SemanticValidationResult)
should extend.
"""

from pydantic import BaseModel


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


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass
