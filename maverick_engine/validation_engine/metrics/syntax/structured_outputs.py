from maverick_engine.validation_engine.metrics.validation_result import ValidationResult


class SyntaxValidationResult(ValidationResult):
    """
    Result of parsing a metrics query expression.

    Extends the base ValidationResult with syntax-specific fields for error location
    and context information.

    Attributes:
        is_valid: Inherited from ValidationResult - True if syntax is valid
        error: Inherited from ValidationResult - Error message if validation failed
        line: Line number where syntax error occurred (1-indexed)
        column: Column number where syntax error occurred (1-indexed)
        context: Contextual snippet around the error location
    """
    line: int | None = None
    column: int | None = None
    context: str | None = None

    @classmethod
    def success(cls) -> "SyntaxValidationResult":
        return cls(is_valid=True)

    @classmethod
    def failure(
        cls,
        message: str,
        *,
        line: int | None = None,
        column: int | None = None,
        context: str | None = None,
    ) -> "SyntaxValidationResult":
        return cls(is_valid=False, error=message, line=line, column=column, context=context)