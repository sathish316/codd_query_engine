from typing import Protocol

from maverick_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent


class MetricsQuerygenPreprocessor(Protocol):
    """
    Protocol for preprocessing and normalizing query intents.

    Implementations can enrich intents with defaults, validate inputs,
    or apply business rules for transformation before query generation.
    """

    def preprocess(self, intent: MetricsQueryIntent) -> MetricsQueryIntent:
        """
        Preprocess and normalize the given query intent.

        Args:
            intent: The raw query intent to preprocess

        Returns:
            A normalized query intent ready for query generation
        """
        ...
