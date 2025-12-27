from typing import Protocol


class MetricExpressionParseError(Exception):
    """Raised when a metric expression cannot be parsed."""

    pass


class MetricExpressionParser(Protocol):
    """
    Protocol for parsing metric expressions to extract metric names.

    Implementations should be synchronous and raise MetricExpressionParseError
    or generic Exception on parse failures.
    """

    def parse(self, metric_expression: str) -> set[str]:
        """
        Parse a metric expression and extract unique metric names.

        Args:
            metric_expression: The expression string to parse

        Returns:
            Set of unique metric names found in the expression

        Raises:
            MetricExpressionParseError: If the expression is malformed
        """
        ...
