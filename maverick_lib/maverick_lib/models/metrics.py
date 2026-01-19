"""Pydantic models for metrics queries."""

from pydantic import BaseModel, Field
from typing import Optional


class QueryOpts(BaseModel):
    """Query options for controlling query generation behavior."""

    spring_micrometer_transform: bool = Field(
        default=False,
        description="Whether to apply Spring Micrometer metric name transformations",
    )


class MetricsQueryIntent(BaseModel):
    """Pydantic model for PromQL query generation intent.

    This model is used by both the REST API and MCP server for type-safe
    request handling.
    """

    description: str = Field(..., description="What you want to query")
    namespace: str = Field(..., description="Prometheus namespace")
    metric_name: str = Field(..., description="Specific metric to query")
    meter_type: Optional[str] = Field(
        None, description="Type of meter (counter, gauge, histogram, summary)"
    )
    aggregation: Optional[str] = Field(
        None, description="Aggregation function like 'rate', 'sum', 'avg'"
    )
    group_by: Optional[list[str]] = Field(None, description="Labels to group by")
    filters: Optional[dict[str, str]] = Field(
        None, description="Label filters as key-value pairs"
    )
    window: Optional[str] = Field(
        "5m",
        description="Time range window (e.g., '1m', '5m', '1h'). Range queries select a range of samples back from the current instant.",
    )
    service: str = Field(..., description="Service name to filter metrics")
    query_opts: Optional[QueryOpts] = Field(
        None, description="Query generation options"
    )
