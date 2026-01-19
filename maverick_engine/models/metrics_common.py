from typing import TypedDict


class MetricMetadata(TypedDict, total=False):
    """Type definition for metric metadata."""

    metric_name: str  # Required
    description: str | None
    unit: str | None
    category: str | None
    subcategory: str | None
    category_description: str | None
    golden_signal_type: str | None
    golden_signal_description: str | None
    meter_type: str | None
    meter_type_description: str | None
