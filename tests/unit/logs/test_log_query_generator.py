import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from maverick_engine.logs.log_patterns import LogPattern
from maverick_engine.querygen_engine.logs.log_query_generator import LogQueryGenerator
from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent


def test_generate_loki_query():
    intent = LogQueryIntent(
        description="timeout errors",
        backend="loki",
        patterns=[LogPattern(pattern="timeout", level="error")],
        service="payments",
    )

    result = LogQueryGenerator().generate(intent)

    assert result.backend == "loki"
    assert (
        '{service="payments"' in result.query or '{service="payments"}' in result.query
    )
    assert "timeout" in result.query


def test_generate_splunk_query():
    intent = LogQueryIntent(
        description="request failures",
        backend="splunk",
        patterns=[LogPattern(pattern="failed request", level="warn")],
        service="api-gateway",
    )

    result = LogQueryGenerator().generate(intent)

    assert result.backend == "splunk"
    assert result.query.startswith("search")
    assert "api-gateway" in result.query
    assert "failed request" in result.query
