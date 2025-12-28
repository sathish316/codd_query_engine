"""Splunk SPL syntax validator using a minimal Lark grammar."""

from __future__ import annotations

from maverick_engine.validation_engine.grammar_validator import (
    GrammarValidator,
    SyntaxValidationResult,
)


class SplunkSPLSyntaxValidator:
    """Validates Splunk SPL syntax by parsing against a simplified grammar."""

    def __init__(self):
        self._validator = GrammarValidator("logs/splunk_spl_grammar.lark", "Splunk SPL")

    def validate(self, query: str) -> SyntaxValidationResult:
        return self._validator.validate(query)
