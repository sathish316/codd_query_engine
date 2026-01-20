"""Main configuration for Codd MCP Server."""

from pathlib import Path

from pydantic import BaseModel, Field
from opus_agent_base.config.config_manager import ConfigManager
from codd_lib.config.semantic_store_config import SemanticStoreConfig
from codd_lib.config.redis_config import RedisConfig
from codd_lib.config.loki_config import LokiConfig
from codd_lib.config.splunk_config import SplunkConfig
from codd_lib.config.prometheus_config import PrometheusConfig
from codd_lib.config.cache_config import QuerygenCacheConfig
from codd_lib.config.debug_config import DebugConfig
from codd_engine.utils.file_utils import expand_path

DEFAULT_CONFIG_PATH = expand_path("$HOME/.codd/config.yml")


class CoddConfig(BaseModel):
    """Configuration for Codd MCP Server."""

    config_path: str = Field(default=DEFAULT_CONFIG_PATH)
    semantic_store: SemanticStoreConfig = Field(default_factory=SemanticStoreConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    loki: LokiConfig = Field(default_factory=LokiConfig)
    splunk: SplunkConfig = Field(default_factory=SplunkConfig)
    prometheus: PrometheusConfig = Field(default_factory=PrometheusConfig)
    querygen_cache: QuerygenCacheConfig = Field(default_factory=QuerygenCacheConfig)
    debug: DebugConfig = Field(default_factory=DebugConfig)

    @classmethod
    def from_config_file(cls, config_path: str = DEFAULT_CONFIG_PATH) -> "CoddConfig":
        """Load CoddConfig from a YAML config file using ConfigManager.

        Args:
            config_path: Path to the config file (default: ~/.codd/config.yml)

        Returns:
            CoddConfig instance populated with values from the config file
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
            debug=config_manager.get_setting_as_model("debug", DebugConfig),
        )
