"""Codd Client Library - Reusable observability client."""

from codd_lib.client import (
    CoddClient,
    MetricsClient,
    MetricsPromQLClient,
    LogsClient,
    LogsLogQLClient,
    LogsSplunkClient,
)
from codd_lib.config import (
    CoddConfig,
    PrometheusConfig,
    LokiConfig,
    SplunkConfig,
    RedisConfig,
    SemanticStoreConfig,
)
from codd_lib.models import (
    MetricsQueryIntent,
    QueryOpts,
    LogQueryIntent,
    LogPattern,
)

__all__ = [
    # Clients
    "CoddClient",
    "MetricsClient",
    "MetricsPromQLClient",
    "LogsClient",
    "LogsLogQLClient",
    "LogsSplunkClient",
    # Configs
    "CoddConfig",
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
