"""Neo4j Cypher syntax validator using Lark grammar."""

from __future__ import annotations

from maverick_engine.validation_engine.grammar_validator import (
    GrammarValidator,
    SyntaxValidationResult,
)


class CypherSyntaxValidator:
    """Validates Neo4j Cypher syntax by parsing against Cypher grammar."""

    def __init__(self):
        self._validator = GrammarValidator("graph/cypher_grammar.lark", "Cypher")

    def validate(self, query: str) -> SyntaxValidationResult:
        """
        Validate a Cypher query for syntax correctness.

        Args:
            query: The Cypher query string to validate

        Returns:
            SyntaxValidationResult with validation status and error details if invalid
        """
        return self._validator.validate(query)
