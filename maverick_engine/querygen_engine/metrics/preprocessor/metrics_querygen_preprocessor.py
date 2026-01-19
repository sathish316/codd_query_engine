from typing import Protocol

from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent, QueryOpts


class MetricsQuerygenPreprocessor(Protocol):
    """
    Protocol for preprocessing and normalizing query intents.

    Implementations can enrich intents with defaults, validate inputs,
    or apply business rules for transformation before query generation.
    """

    def preprocess(
        self, intent: MetricsQueryIntent, query_opts: QueryOpts | None = None
    ) -> MetricsQueryIntent:
        """
        Preprocess and normalize the given query intent.

        Args:
            intent: The raw query intent to preprocess
            query_opts: Optional query options for controlling preprocessing behavior

        Returns:
            A normalized query intent ready for query generation
        """
        ...
