import logging
from dataclasses import dataclass, field
from typing import Optional, TypedDict

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


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
    along with a confidence score indicating extraction reliability.
    """
    metric_names: list[str]
    confidence: float

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

    @field_validator('confidence', mode='before')
    @classmethod
    def clamp_confidence(cls, v):
        """Clamp confidence to valid range [0.0, 1.0]."""
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (TypeError, ValueError):
            return 0.0

@dataclass
#TODO: use BaseModel
class SchemaValidationResult:
    """
    Result of schema validation for a metric expression.

    Attributes:
        is_valid: True if all metrics exist in namespace, False otherwise
        invalid_metrics: List of metric names not found in namespace
        error: Optional error message for parser failures or other issues
    """
    is_valid: bool
    invalid_metrics: list[str] = field(default_factory=list)
    error: Optional[str] = None

    @classmethod
    def success(cls) -> "SchemaValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True, invalid_metrics=[])

    @classmethod
    def failure(cls, invalid_metrics: list[str], namespace: str) -> "SchemaValidationResult":
        """Create a failure result with invalid metrics."""
        error_msg = cls._build_error_message(invalid_metrics, namespace)
        return cls(is_valid=False, invalid_metrics=invalid_metrics, error=error_msg)

    @classmethod
    def parse_error(cls, message: str, original_exception: Optional[Exception] = None) -> "SchemaValidationResult":
        """Create a result for parser failures."""
        error_msg = f"Expression parse error: {message}"
        if original_exception:
            logger.warning(
                "Parser exception during schema validation",
                exc_info=original_exception
            )
        return cls(is_valid=False, invalid_metrics=[], error=error_msg)

    @staticmethod
    def _build_error_message(invalid_metrics: list[str], namespace: str, max_display: int = 5) -> str:
        """Build a formatted error message for invalid metrics."""
        count = len(invalid_metrics)
        if count == 0:
            return ""

        displayed = invalid_metrics[:max_display]
        metrics_str = ", ".join(f"'{m}'" for m in displayed)

        if count > max_display:
            return f"Found {count} invalid metrics in namespace '{namespace}': {metrics_str}, and {count - max_display} more"
        return f"Found {count} invalid metric(s) in namespace '{namespace}': {metrics_str}"
