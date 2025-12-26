"""
Structured output models for LogQL parsing and validation.
"""

from pydantic import BaseModel, field_validator


class LogQLExtractionResponse(BaseModel):
    """
    Response schema for LogQL stream selector extraction.

    Contains the stream selectors extracted from a LogQL expression
    along with a confidence score indicating extraction reliability.
    """
    stream_selectors: dict[str, list[str]]  # label_name -> list of values
    confidence: float

    @field_validator('stream_selectors', mode='before')
    @classmethod
    def normalize_selectors(cls, v):
        """Normalize stream selectors: strip whitespace, remove empties."""
        if not isinstance(v, dict):
            return {}

        normalized = {}
        for label_name, values in v.items():
            if isinstance(label_name, str) and isinstance(values, list):
                clean_label = label_name.strip()
                if clean_label:
                    clean_values = []
                    for val in values:
                        if isinstance(val, str):
                            clean_val = val.strip()
                            if clean_val:
                                clean_values.append(clean_val)
                    if clean_values:
                        normalized[clean_label] = clean_values
        return normalized

    @field_validator('stream_selectors', mode='after')
    @classmethod
    def dedupe_values(cls, v):
        """Remove duplicate values for each label while preserving order."""
        deduped = {}
        for label_name, values in v.items():
            seen = set()
            deduped_values = []
            for val in values:
                if val not in seen:
                    seen.add(val)
                    deduped_values.append(val)
            deduped[label_name] = deduped_values
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
