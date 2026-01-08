"""Protocol for graph syntax validators."""

from __future__ import annotations

from typing import Protocol

from maverick_engine.validation_engine.grammar_validator import SyntaxValidationResult


class GraphSyntaxValidator(Protocol):
    """Validates syntax for a graph query language."""

    def validate(self, query: str) -> SyntaxValidationResult: ...
