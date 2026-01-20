"""
Log pattern data structures used by discovery, query generation, and validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class LogPattern:
    """Represents a structured log pattern."""

    pattern: str
    level: str = "info"
    source: Optional[str] = None
    description: Optional[str] = None
