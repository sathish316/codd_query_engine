from dataclasses import dataclass

@dataclass(frozen=True)
class SyntaxValidationResult:
    """Result of parsing a metrics query expression."""

    is_valid: bool
    error: str | None = None
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