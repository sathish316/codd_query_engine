from __future__ import annotations

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import LogQueryResult


class LogQLQueryGeneratorAgent:
    """Generate basic LogQL log queries."""

    def generate(self, intent: LogQueryIntent) -> LogQueryResult:
        selectors = []
        levels = {pattern.level for pattern in intent.patterns if pattern.level}
        if intent.service:
            selectors.append(f'service="{intent.service}"')
        if levels:
            escaped_levels = "|".join(sorted(levels))
            selectors.append(f'level=~"{escaped_levels}"')

        selector_str = "{" + ", ".join(selectors) + "}" if selectors else "{}"

        # Build a single regex that ORs all patterns for efficiency
        pattern_terms = [p.pattern for p in intent.patterns if p.pattern]
        pattern_regex = (
            "|".join(sorted(set(pattern_terms)))
            if pattern_terms
            else intent.description
        )
        pipeline = ""
        if pattern_regex:
            pipeline = f' |~ "{pattern_regex}"'

        query = f"{selector_str}{pipeline}"
        return LogQueryResult(
            query=query,
            backend="loki",
            used_patterns=pattern_terms,
            levels=sorted(levels),
            selector=selector_str,
        )
