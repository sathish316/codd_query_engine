from __future__ import annotations

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import LogQueryResult


class SplunkSPLQueryGenerator:
    """Generate basic Splunk SPL log queries."""

    def generate(self, intent: LogQueryIntent) -> LogQueryResult:
        pattern_terms = [p.pattern for p in intent.patterns if p.pattern]
        pattern_clause = ""
        if pattern_terms:
            joined_patterns = " OR ".join(
                [f'"{p}"' for p in sorted(set(pattern_terms))]
            )
            pattern_clause = f"({joined_patterns})"

        level_clause = ""
        levels = {pattern.level for pattern in intent.patterns if pattern.level}
        if levels:
            joined_levels = " OR ".join([f'level="{lvl}"' for lvl in sorted(levels)])
            level_clause = f"({joined_levels})"

        service_clause = f'service="{intent.service}"' if intent.service else ""

        clauses = [c for c in (pattern_clause, level_clause, service_clause) if c]
        search_head = (
            "search " + " ".join(clauses)
            if clauses
            else f'search "{intent.description}"'
        )
        query = search_head + f" | head {intent.limit}"

        return LogQueryResult(
            query=query,
            backend="splunk",
            used_patterns=pattern_terms,
            levels=sorted(levels),
            selector=None,
        )
