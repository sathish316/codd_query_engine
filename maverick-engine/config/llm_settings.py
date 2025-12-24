"""
LLM configuration settings module.

Centralizes model configuration for PydanticAI-based metric expression parsing.
Loads settings from environment variables with sensible defaults.

Required environment variables:
    OPENAI_API_KEY: API key for OpenAI services

Optional environment variables:
    OPENAI_MODEL_NAME: Model name (default: gpt-4o-mini)
    OPENAI_TEMPERATURE: Temperature for sampling (default: 0.0)
    OPENAI_MAX_TOKENS: Maximum tokens for response (default: 256)
    OPENAI_TIMEOUT: Request timeout in seconds (default: 30)
    LLM_MAX_RETRIES: Maximum retry attempts for transient errors (default: 3)
    LLM_CONFIDENCE_THRESHOLD: Minimum confidence score to accept (default: 0.7)
"""

import os
from dataclasses import dataclass, field
from typing import Optional


# TODO: replace LLMSettings with ConfigManager
@dataclass(frozen=True)
class LLMSettings:
    """
    Configuration settings for LLM-based metric expression parsing.

    Attributes:
        api_key: OpenAI API key (required for production use)
        model_name: Model identifier for OpenAI API
        temperature: Sampling temperature (lower = more deterministic)
        max_tokens: Maximum tokens in response
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for transient errors
        confidence_threshold: Minimum confidence to accept LLM response
    """
    api_key: Optional[str] = None
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 256
    timeout: int = 30
    max_retries: int = 3
    confidence_threshold: float = 0.7

    def __post_init__(self):
        """Validate settings after initialization."""
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
        if self.timeout < 1:
            raise ValueError(f"timeout must be positive, got {self.timeout}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {self.max_retries}")
        if self.confidence_threshold < 0.0 or self.confidence_threshold > 1.0:
            raise ValueError(f"confidence_threshold must be between 0.0 and 1.0, got {self.confidence_threshold}")

    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and len(self.api_key.strip()) > 0


def load_llm_settings() -> LLMSettings:
    """
    Load LLM settings from environment variables.

    Returns:
        LLMSettings instance with values from environment or defaults.

    Environment Variables:
        OPENAI_API_KEY: Required for production, optional for testing
        OPENAI_MODEL_NAME: Model identifier (default: gpt-4o-mini)
        OPENAI_TEMPERATURE: Sampling temperature (default: 0.0)
        OPENAI_MAX_TOKENS: Max response tokens (default: 256)
        OPENAI_TIMEOUT: Request timeout seconds (default: 30)
        LLM_MAX_RETRIES: Retry attempts (default: 3)
        LLM_CONFIDENCE_THRESHOLD: Min confidence (default: 0.7)
    """
    def get_float(key: str, default: float) -> float:
        val = os.environ.get(key)
        if val is None:
            return default
        try:
            return float(val)
        except ValueError:
            return default

    def get_int(key: str, default: int) -> int:
        val = os.environ.get(key)
        if val is None:
            return default
        try:
            return int(val)
        except ValueError:
            return default

    return LLMSettings(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model_name=os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        temperature=get_float("OPENAI_TEMPERATURE", 0.0),
        max_tokens=get_int("OPENAI_MAX_TOKENS", 256),
        timeout=get_int("OPENAI_TIMEOUT", 30),
        max_retries=get_int("LLM_MAX_RETRIES", 3),
        confidence_threshold=get_float("LLM_CONFIDENCE_THRESHOLD", 0.7),
    )
