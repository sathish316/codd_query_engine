"""Configuration for Loki."""

from pydantic import BaseModel


class LokiConfig(BaseModel):
    """Configuration for Loki client."""

    base_url: str = "http://localhost:3100"
    timeout: int = 30
    service_label: str = "service"
