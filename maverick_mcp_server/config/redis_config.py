"""Configuration for Redis."""

from pydantic import BaseModel


class RedisConfig(BaseModel):
    """Configuration for Redis client."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    decode_responses: bool = True
