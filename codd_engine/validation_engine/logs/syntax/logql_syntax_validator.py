"""LogQL syntax validator using a minimal Lark grammar."""

from __future__ import annotations

from codd_engine.validation_engine.grammar_validator import (
    GrammarValidator,
    SyntaxValidationResult,
)


class LogQLSyntaxValidator:
    """Validates LogQL syntax by parsing against a simplified grammar."""

    def __init__(self):
        self._validator = GrammarValidator("logs/logql_grammar.lark", "LogQL")

    def validate(self, query: str) -> SyntaxValidationResult:
        return self._validator.validate(query)
