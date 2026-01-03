"""Configuration for Splunk."""

from pydantic import BaseModel


class SplunkConfig(BaseModel):
    """Configuration for Splunk client."""

    base_url: str = "https://localhost:8089"
    timeout: int = 30
    # Optional authentication token for Splunk API
    auth_token: str | None = None
    # Optional default index to search
    index: str | None = None
