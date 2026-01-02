"""Maverick client library for MCP server and other integrations."""

from maverick_mcp_server.client.maverick_client import MaverickClient
from maverick_mcp_server.client.metrics_client import MetricsClient
from maverick_mcp_server.client.metrics_promql_client import MetricsPromQLClient
from maverick_mcp_server.client.logs_client import LogsClient
from maverick_mcp_server.client.logs_logql_client import LogsLogQLClient
from maverick_mcp_server.client.promql_module import PromQLModule
from maverick_mcp_server.client.logql_module import LogQLModule
from maverick_mcp_server.client.opus_module import OpusModule

__all__ = [
    "MaverickClient",
    "MetricsClient",
    "MetricsPromQLClient",
    "LogsClient",
    "LogsLogQLClient",
    "PromQLModule",
    "LogQLModule",
    "OpusModule",
]
