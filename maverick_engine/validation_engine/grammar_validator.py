"""Generic grammar-based validator using Lark parser."""

from __future__ import annotations

import logging
from pathlib import Path

from lark import Lark
from lark.exceptions import LarkError, UnexpectedInput
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Base path for grammar files
GRAMMAR_BASE_PATH = Path(__file__).parent.parent / "grammar"


class SyntaxValidationResult(BaseModel):
    """Result of syntax validation for any query language."""

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
        line: int | None = None,
        column: int | None = None,
        context: str | None = None,
    ) -> "SyntaxValidationResult":
        return cls(
            is_valid=False, error=message, line=line, column=column, context=context
        )


class GrammarValidator:
    """Validates query syntax using a Lark grammar file."""

    def __init__(self, grammar_file: str, language_name: str):
        """
        Args:
            grammar_file: Path to grammar file relative to the grammar directory
                          (e.g., "logs/logql_grammar.lark")
            language_name: Display name for error messages (e.g., "LogQL")
        """
        self._grammar_file = grammar_file
        self._language_name = language_name
        self._parser: Lark | None = None

    def _get_parser(self) -> Lark:
        if self._parser is None:
            grammar_path = GRAMMAR_BASE_PATH / self._grammar_file
            self._parser = Lark.open(
                str(grammar_path),
                parser="lalr",
                maybe_placeholders=False,
                propagate_positions=True,
            )
        return self._parser

    def validate(self, query: str) -> SyntaxValidationResult:
        if query is None or not str(query).strip():
            return SyntaxValidationResult.failure(
                f"{self._language_name} query cannot be empty"
            )

        try:
            self._get_parser().parse(query)
            return SyntaxValidationResult.success()
        except UnexpectedInput as exc:
            context = None
            try:
                context = exc.get_context(query, span=80)
            except Exception:
                pass

            message = f"Invalid {self._language_name} syntax"
            if getattr(exc, "line", None) and getattr(exc, "column", None):
                message = f"{message} at line {exc.line}, column {exc.column}"

            logger.debug(f"{self._language_name} parse error", exc_info=True)
            return SyntaxValidationResult.failure(
                message,
                line=getattr(exc, "line", None),
                column=getattr(exc, "column", None),
                context=context,
            )
        except LarkError as exc:
            logger.debug(f"{self._language_name} parser error", exc_info=True)
            return SyntaxValidationResult.failure(
                f"{self._language_name} parser error: {exc}"
            )
