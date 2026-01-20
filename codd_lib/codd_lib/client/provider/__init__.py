"""Provider modules for dependency injection (Spring-like pattern)."""

from codd_lib.client.provider.promql_module import PromQLModule
from codd_lib.client.provider.logs_module import LogsModule
from codd_lib.client.provider.logql_module import LogQLModule
from codd_lib.client.provider.splunk_module import SplunkModule
from codd_lib.client.provider.opus_module import OpusModule
from codd_lib.client.provider.cache_module import CacheModule

__all__ = [
    "PromQLModule",
    "LogsModule",
    "LogQLModule",
    "SplunkModule",
    "OpusModule",
    "CacheModule",
]
