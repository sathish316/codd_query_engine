"""Configuration for debug settings."""

from pydantic import BaseModel


class DebugConfig(BaseModel):
    """Configuration for debug settings.

    Attributes:
        logfire_enabled: Whether logfire tracing is enabled
    """

    logfire_enabled: bool = False
