from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from maverick_engine.logs.log_patterns import LogPattern
from maverick_engine.querygen_engine.logs.models import LogQueryBackend


@dataclass(slots=True)
class LogQueryIntent:
    """Structured intent for generating a log query."""

    description: str
    backend: LogQueryBackend
    patterns: Sequence[LogPattern]
    service_label: str | None = "service"
    service: str | None = None
    default_level: str = "error"
    limit: int = 200
    namespace: str | None = None
