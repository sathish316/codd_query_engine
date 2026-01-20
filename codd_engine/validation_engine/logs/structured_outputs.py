"""Structured outputs for log query validation."""

from __future__ import annotations

from dataclasses import dataclass

# Re-export unified SyntaxValidationResult
from codd_engine.validation_engine.grammar_validator import SyntaxValidationResult

__all__ = ["SyntaxValidationResult", "LogQueryValidationResult"]


@dataclass(slots=True)
class LogQueryValidationResult:
    syntax: SyntaxValidationResult

    @property
    def passed(self) -> bool:
        return self.syntax.is_valid
