from pydantic import BaseModel, Field
from typing import Optional


class EnrichedMetricMetadata(BaseModel):
    """Structured output for enriched metric metadata."""

    metric_name: str = Field(description="The metric name")
    type: str = Field(description="Metric type: gauge, counter, histogram, timer")
    description: str = Field(
        description="Detailed natural language description of what this metric measures"
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement (e.g., milliseconds, bytes, percent, count)",
    )
    category: str = Field(
        description="High-level category: application, infrastructure, business, etc."
    )
    subcategory: str = Field(
        description="Specific subcategory: http, database, cache, memory, cpu, etc."
    )
    category_description: str = Field(
        description="Description of what the category represents"
    )
    golden_signal_type: str = Field(
        description="Golden signal classification: latency, traffic, errors, saturation, or none"
    )
    golden_signal_description: str = Field(
        description="Explanation of how this metric relates to the golden signal"
    )
    meter_type: str = Field(description="Meter type: gauge, counter, histogram, timer")
    meter_type_description: str = Field(
        description="Explanation of what this meter type represents for this metric"
    )
