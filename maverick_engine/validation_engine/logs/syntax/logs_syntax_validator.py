"""Protocol for log syntax validators."""

from __future__ import annotations

from typing import Protocol

from maverick_engine.validation_engine.grammar_validator import SyntaxValidationResult


class LogsSyntaxValidator(Protocol):
    """Validates syntax for a log query language."""

    def validate(self, query: str) -> SyntaxValidationResult: ...
