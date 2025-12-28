"""Loki LogQL query generator."""

from __future__ import annotations

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import LogQueryResult


class LokiLogQLQueryGenerator:
    """Generates Loki LogQL queries from structured intents."""

    def generate(self, intent: LogQueryIntent) -> LogQueryResult:
        """Generate a LogQL query from the given intent."""
        # Build label selector
        labels = []
        if intent.service:
            labels.append(f'service="{intent.service}"')
        if intent.namespace:
            labels.append(f'namespace="{intent.namespace}"')

        selector = "{" + ", ".join(labels) + "}" if labels else "{}"

        # Build filter pipeline
        filters = []
        used_patterns = []
        levels = []

        for pattern in intent.patterns:
            filters.append(f'|~ "{pattern.pattern}"')
            used_patterns.append(pattern.pattern)
            if pattern.level and pattern.level not in levels:
                levels.append(pattern.level)

        # Add level filter if patterns have levels
        if levels:
            level_regex = "|".join(levels)
            filters.append(f'| level=~"{level_regex}"')

        # Add limit
        filters.append(f"| limit {intent.limit}")

        query = selector + " " + " ".join(filters)

        return LogQueryResult(
            query=query.strip(),
            backend="loki",
            used_patterns=used_patterns,
            levels=levels,
            selector=selector,
        )
