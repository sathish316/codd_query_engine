"""Maverick client library for MCP server and other integrations."""

from maverick_mcp_server.client.maverick_client import MaverickClient
from maverick_mcp_server.client.metrics_client import MetricsClient
from maverick_mcp_server.client.metrics_promql_client import MetricsPromQLClient
from maverick_mcp_server.client.logs_client import LogsClient
from maverick_mcp_server.client.logs_logql_client import LogsLogQLClient
from maverick_mcp_server.client.logs_splunk_client import LogsSplunkClient
from maverick_mcp_server.client.provider import (
    PromQLModule,
    LogQLModule,
    SplunkModule,
    OpusModule,
)

__all__ = [
    "MaverickClient",
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
