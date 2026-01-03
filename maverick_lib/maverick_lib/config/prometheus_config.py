"""Configuration for Prometheus."""

from pydantic import BaseModel


class PrometheusConfig(BaseModel):
    """Configuration for Prometheus client."""

    base_url: str = "http://localhost:9090"
    timeout: int = 30
    # Optional authentication token for Prometheus API
    auth_token: str | None = None
