"""Provider modules for dependency injection (Spring-like pattern)."""

from maverick_lib.client.provider.promql_module import PromQLModule
from maverick_lib.client.provider.logs_module import LogsModule
from maverick_lib.client.provider.logql_module import LogQLModule
from maverick_lib.client.provider.splunk_module import SplunkModule
from maverick_lib.client.provider.opus_module import OpusModule

__all__ = ["PromQLModule", "LogsModule", "LogQLModule", "SplunkModule", "OpusModule"]
