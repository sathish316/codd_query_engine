"""Codd client library for MCP server and other integrations."""

from codd_lib.client.codd_client import CoddClient
from codd_lib.client.metrics_client import MetricsClient
from codd_lib.client.metrics_promql_client import MetricsPromQLClient
from codd_lib.client.logs_client import LogsClient
from codd_lib.client.logs_logql_client import LogsLogQLClient
from codd_lib.client.logs_splunk_client import LogsSplunkClient
from codd_lib.client.provider import (
    PromQLModule,
    LogQLModule,
    SplunkModule,
    OpusModule,
)

__all__ = [
    "CoddClient",
    "MetricsClient",
    "MetricsPromQLClient",
    "LogsClient",
    "LogsLogQLClient",
    "LogsSplunkClient",
    "PromQLModule",
    "LogQLModule",
    "SplunkModule",
    "OpusModule",
]
