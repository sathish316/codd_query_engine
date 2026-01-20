"""PromQL syntax validator using a Lark grammar."""

from __future__ import annotations

from codd_engine.validation_engine.grammar_validator import (
    GrammarValidator,
    SyntaxValidationResult,
)


class PromQLSyntaxValidator:
    """Validates PromQL syntax by parsing against a Lark grammar."""

    def __init__(self):
        self._validator = GrammarValidator("metrics/promql_grammar.lark", "PromQL")

    def validate(self, query: str) -> SyntaxValidationResult:
        return self._validator.validate(query)
