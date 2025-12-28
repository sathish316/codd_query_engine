"""Facade for log query generation dispatching to backend-specific generators."""

from __future__ import annotations

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import LogQueryResult
from maverick_engine.querygen_engine.logs.log_query_generator.loki import (
    LokiLogQLQueryGenerator,
)
from maverick_engine.querygen_engine.logs.log_query_generator.splunk import (
    SplunkSPLQueryGenerator,
)


class LogQueryGenerator:
    """Facade that dispatches to backend-specific generators."""

    def generate(self, intent: LogQueryIntent) -> LogQueryResult:
        if intent.backend == "loki":
            generator = LokiLogQLQueryGenerator()
        elif intent.backend == "splunk":
            generator = SplunkSPLQueryGenerator()
        else:
            raise ValueError(f"Unsupported backend: {intent.backend}")

        return generator.generate(intent)
