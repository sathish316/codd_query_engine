from typing import TypedDict

from pydantic import BaseModel, field_validator


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

class MetricExtractionResponse(BaseModel):
    """
    Response schema for metric name extraction.

    Contains the list of metric names extracted from an expression
    """
    metric_names: list[str]

    @field_validator('metric_names', mode='before')
    @classmethod
    def normalize_metric_names(cls, v):
        """Normalize metric names: lowercase, strip whitespace, remove empties."""
        if not isinstance(v, list):
            return []
        normalized = []
        for name in v:
            if isinstance(name, str):
                clean = name.strip().lower()
                if clean:
                    normalized.append(clean)
        return normalized

    @field_validator('metric_names', mode='after')
    @classmethod
    def dedupe_metric_names(cls, v):
        """Remove duplicate metric names while preserving order."""
        #TODO: use set and remove dedup method
        seen = set()
        deduped = []
        for name in v:
            if name not in seen:
                seen.add(name)
                deduped.append(name)
        return deduped

class SemanticValidationResult(BaseModel):
    """
    Response schema for semantic validation of PromQL query intent.

    Compares the original query intent with the actual behavior of the generated query
    to determine if they match semantically.
    """
    intent_match: bool
    partial_match: bool
    explanation: str
    original_intent_summary: str
    actual_query_behavior: str
    confidence: float  # 0.0 to 1.0
