from dataclasses import dataclass, field


@dataclass(frozen=True)
class AggregationFunctionSuggestion:
    """
    Suggested aggregation function with optional parameters.

    Represents a recommended PromQL aggregation function based on metric type,
    including any required or suggested parameters for that function.
    """

    function_name: str
    params: dict[str, str | float | list[str] | list[float]] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class MetricsQueryIntent:
    """
    Structured request for generating a PromQL query.

    This class mirrors the intent-first approach used by Opus Agents and lets
    us enrich or validate user asks before hitting an LLM.
    """

    metric: str
    metric_type: str = "gauge"
    filters: dict[str, str] = field(default_factory=dict)
    window: str = "5m"
    group_by: list[str] = field(default_factory=list)
    aggregation_suggestions: list[AggregationFunctionSuggestion] | None = None

    def clone_with(self, **updates) -> "MetricsQueryIntent":
        """Return a new intent with updated fields."""
        data = self.__dict__ | updates
        return MetricsQueryIntent(**data)
