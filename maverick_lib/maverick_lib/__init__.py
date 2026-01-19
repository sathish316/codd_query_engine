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
from maverick_lib.models import (
    MetricsQueryIntent,
    QueryOpts,
    LogQueryIntent,
    LogPattern,
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
    # Models
    "MetricsQueryIntent",
    "QueryOpts",
    "LogQueryIntent",
    "LogPattern",
]

__version__ = "0.1.0"
