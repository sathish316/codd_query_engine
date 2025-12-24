from typing import TypedDict


# TODO: use MetricMetadata in SearchResult
class SearchResult(TypedDict):
    """Type definition for search results."""
    metric_name: str
    similarity_score: float
    type: str
    description: str
    unit: str
    category: str
    subcategory: str
    category_description: str
    golden_signal_type: str
    golden_signal_description: str
    meter_type: str
    meter_type_description: str

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass
