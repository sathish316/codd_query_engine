from __future__ import annotations

from dataclasses import dataclass, field

from maverick_engine.querygen_engine.logs.models import LogQueryBackend


@dataclass(slots=True)
class LogQueryResult:
    """Generated query alongside basic metadata."""

    query: str
    backend: LogQueryBackend
    used_patterns: list[str] = field(default_factory=list)
    levels: list[str] = field(default_factory=list)
    selector: str | None = None
