"""
PromQL syntax validator.

This module provides a lightweight PromQL grammar-based validator using Lark.
It validates that a query is syntactically well-formed (not semantically valid).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from lark import Lark
from lark.exceptions import LarkError, UnexpectedInput

from maverick_engine.validation_engine.metrics.syntax.metrics_syntax_validator import (
    MetricsSyntaxValidator,
)
from maverick_engine.validation_engine.metrics.syntax.structured_outputs import (
    SyntaxValidationResult,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _promql_parser() -> Lark:
    grammar_path = (
        Path(__file__).parent / "../../../grammar/metrics/promql_grammar.lark"
    )
    print(f"Grammar path: {grammar_path}")
    return Lark.open(
        str(grammar_path),
        parser="lalr",
        maybe_placeholders=False,
        propagate_positions=True,
    )


class PromQLSyntaxValidator(MetricsSyntaxValidator):
    """Validates PromQL syntax by parsing against a Lark grammar."""

    def validate(self, query: str) -> SyntaxValidationResult:
        if query is None or not query.strip():
            return SyntaxValidationResult.failure("PromQL query cannot be empty")

        try:
            _promql_parser().parse(query)
            return SyntaxValidationResult.success()
        except UnexpectedInput as e:
            context = None
            try:
                context = e.get_context(query, span=80)
            except Exception:
                context = None

            message = "Invalid PromQL syntax"
            if getattr(e, "line", None) and getattr(e, "column", None):
                message = f"{message} at line {e.line}, column {e.column}"

            logger.debug("PromQL parse error", exc_info=True)
            return SyntaxValidationResult.failure(
                message,
                line=getattr(e, "line", None),
                column=getattr(e, "column", None),
                context=context,
            )
        except LarkError as e:
            logger.debug("PromQL parser error", exc_info=True)
            return SyntaxValidationResult.failure(f"PromQL parser error: {e}")
