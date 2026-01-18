"""Main configuration for Maverick MCP Server."""

from pathlib import Path

from pydantic import BaseModel, Field
from opus_agent_base.config.config_manager import ConfigManager
from maverick_lib.config.semantic_store_config import SemanticStoreConfig
from maverick_lib.config.redis_config import RedisConfig
from maverick_lib.config.loki_config import LokiConfig
from maverick_lib.config.splunk_config import SplunkConfig
from maverick_lib.config.prometheus_config import PrometheusConfig
from maverick_lib.config.cache_config import QuerygenCacheConfig
from maverick_engine.utils.file_utils import expand_path

DEFAULT_CONFIG_PATH = expand_path("$HOME/.maverick/config.yml")


class MaverickConfig(BaseModel):
    """Configuration for Maverick MCP Server."""

    config_path: str = Field(default=DEFAULT_CONFIG_PATH)
    semantic_store: SemanticStoreConfig = Field(default_factory=SemanticStoreConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    loki: LokiConfig = Field(default_factory=LokiConfig)
    splunk: SplunkConfig = Field(default_factory=SplunkConfig)
    prometheus: PrometheusConfig = Field(default_factory=PrometheusConfig)
    querygen_cache: QuerygenCacheConfig = Field(default_factory=QuerygenCacheConfig)

    @classmethod
    def from_config_file(cls, config_path: str = DEFAULT_CONFIG_PATH) -> "MaverickConfig":
        """Load MaverickConfig from a YAML config file using ConfigManager.

        Args:
            config_path: Path to the config file (default: ~/.maverick/config.yml)

        Returns:
            MaverickConfig instance populated with values from the config file
        """
        path = Path(config_path).expanduser()
        config_manager = ConfigManager(str(path.parent), path.name)

        return cls(
            config_path=config_path,
            semantic_store=config_manager.get_setting_as_model(
                "semantic_store", SemanticStoreConfig
            ),
            redis=config_manager.get_setting_as_model("redis", RedisConfig),
            loki=config_manager.get_setting_as_model("loki", LokiConfig),
            splunk=config_manager.get_setting_as_model("splunk", SplunkConfig),
            prometheus=config_manager.get_setting_as_model("prometheus", PrometheusConfig),
            querygen_cache=config_manager.get_setting_as_model(
                "querygen_cache", QuerygenCacheConfig
            ),
        )
