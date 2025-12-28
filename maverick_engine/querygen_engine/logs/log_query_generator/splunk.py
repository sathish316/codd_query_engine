"""Splunk SPL query generator."""

from __future__ import annotations

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import LogQueryResult


class SplunkSPLQueryGenerator:
    """Generates Splunk SPL queries from structured intents."""

    def generate(self, intent: LogQueryIntent) -> LogQueryResult:
        """Generate a Splunk SPL query from the given intent."""
        # Build search command
        parts = ["search"]
        used_patterns = []
        levels = []

        # Add service filter
        if intent.service:
            parts.append(f'service="{intent.service}"')

        # Add namespace filter
        if intent.namespace:
            parts.append(f'namespace="{intent.namespace}"')

        # Build pattern matches
        pattern_clauses = []
        for pattern in intent.patterns:
            pattern_clauses.append(f'"{pattern.pattern}"')
            used_patterns.append(pattern.pattern)
            if pattern.level and pattern.level not in levels:
                levels.append(pattern.level)

        if pattern_clauses:
            parts.append("(" + " OR ".join(pattern_clauses) + ")")

        # Add level filter
        if levels:
            level_clause = " OR ".join(f'level="{lvl}"' for lvl in levels)
            parts.append(f"({level_clause})")

        query = " ".join(parts)

        # Add head limit
        query += f" | head {intent.limit}"

        return LogQueryResult(
            query=query,
            backend="splunk",
            used_patterns=used_patterns,
            levels=levels,
            selector=None,
        )
