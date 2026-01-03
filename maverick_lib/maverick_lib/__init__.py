"""Maverick Client Library - Reusable observability client."""

from maverick_lib.client import (
    MaverickClient,
    MetricsClient,
    MetricsPromQLClient,
    LogsClient,
    LogsLogQLClient,
    LogsSplunkClient,
)
from maverick_lib.config import (
    MaverickConfig,
    PrometheusConfig,
    LokiConfig,
    SplunkConfig,
    RedisConfig,
    SemanticStoreConfig,
)

__all__ = [
    # Clients
    "MaverickClient",
    "MetricsClient",
    "MetricsPromQLClient",
    "LogsClient",
    "LogsLogQLClient",
    "LogsSplunkClient",
    # Configs
    "MaverickConfig",
    "PrometheusConfig",
    "LokiConfig",
    "SplunkConfig",
    "RedisConfig",
    "SemanticStoreConfig",
]

__version__ = "0.1.0"
