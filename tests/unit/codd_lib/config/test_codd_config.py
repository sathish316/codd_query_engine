"""Unit tests for CoddConfig."""

from codd_lib.config import (
    CoddConfig,
    PrometheusConfig,
    LokiConfig,
    SplunkConfig,
    RedisConfig,
    SemanticStoreConfig,
)


def test_codd_config_defaults():
    """Test CoddConfig initializes with default values."""
    config = CoddConfig()

    assert config.config_path is not None
    assert isinstance(config.semantic_store, SemanticStoreConfig)
    assert isinstance(config.redis, RedisConfig)
    assert isinstance(config.loki, LokiConfig)
    assert isinstance(config.splunk, SplunkConfig)
    assert isinstance(config.prometheus, PrometheusConfig)


def test_codd_config_custom_values():
    """Test CoddConfig with custom values."""
    config = CoddConfig(
        config_path="/custom/path/config.yml",
        prometheus=PrometheusConfig(base_url="https://custom-prometheus.com"),
        loki=LokiConfig(base_url="https://custom-loki.com"),
    )

    assert config.config_path == "/custom/path/config.yml"
    assert config.prometheus.base_url == "https://custom-prometheus.com"
    assert config.loki.base_url == "https://custom-loki.com"


def test_prometheus_config_defaults():
    """Test PrometheusConfig defaults."""
    config = PrometheusConfig()

    assert config.base_url == "http://localhost:9090"
    assert config.timeout == 30
    assert config.auth_token is None


def test_loki_config_defaults():
    """Test LokiConfig defaults."""
    config = LokiConfig()

    assert config.base_url == "http://localhost:3100"
    assert config.timeout == 30


def test_splunk_config_defaults():
    """Test SplunkConfig defaults."""
    config = SplunkConfig()

    assert config.base_url == "https://localhost:8089"
    assert config.timeout == 30
    assert config.auth_token is None
    assert config.index is None


def test_redis_config_defaults():
    """Test RedisConfig defaults."""
    config = RedisConfig()

    assert config.host == "localhost"
    assert config.port == 6380
    assert config.db == 0


def test_semantic_store_config_defaults():
    """Test SemanticStoreConfig defaults."""
    config = SemanticStoreConfig()

    assert config.chromadb_host == "localhost"
    assert config.chromadb_port == 8000
