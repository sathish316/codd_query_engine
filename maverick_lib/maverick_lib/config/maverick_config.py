"""Main configuration for Maverick MCP Server."""

from pydantic import BaseModel, Field
from maverick_lib.config.semantic_store_config import SemanticStoreConfig
from maverick_lib.config.redis_config import RedisConfig
from maverick_lib.config.loki_config import LokiConfig
from maverick_lib.config.splunk_config import SplunkConfig
from maverick_lib.config.prometheus_config import PrometheusConfig
from maverick_engine.utils.file_utils import expand_path


class MaverickConfig(BaseModel):
    """Configuration for Maverick MCP Server."""

    config_path: str = Field(default=expand_path("$HOME/.maverick/config.yml"))
    semantic_store: SemanticStoreConfig = Field(default_factory=SemanticStoreConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    loki: LokiConfig = Field(default_factory=LokiConfig)
    splunk: SplunkConfig = Field(default_factory=SplunkConfig)
    prometheus: PrometheusConfig = Field(default_factory=PrometheusConfig)
