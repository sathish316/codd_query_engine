import asyncio
import json

import pytest

from maverick_mcp_server import server


class DummyQueryResult:
    def __init__(self, query: str, success: bool = True) -> None:
        self.query = query
        self.success = success


class DummyMetricsClient:
    def search_relevant_metrics(self, problem_json: str, limit: int = 5) -> list[dict]:
        return [
            {
                "metric_name": "http_requests_total",
                "relevance_score": 0.9,
                "description": "Total HTTP requests",
            }
        ]

    def construct_promql_query(self, intent) -> DummyQueryResult:
        return DummyQueryResult("rate(http_requests_total[5m])")


class DummyLogQLClient:
    def construct_logql_query(self, intent) -> DummyQueryResult:
        return DummyQueryResult('{service="payments"} |~ "error"')


class DummySplunkClient:
    def construct_spl_query(self, intent) -> DummyQueryResult:
        return DummyQueryResult('search service="payments" "timeout" | head 200')


class DummyLogsClient:
    def __init__(self) -> None:
        self.logql = DummyLogQLClient()
        self.splunk = DummySplunkClient()


class DummyMaverickClient:
    def __init__(self) -> None:
        self.metrics = DummyMetricsClient()
        self.logs = DummyLogsClient()


@pytest.mark.integration
def test_search_relevant_metrics_happy_path(monkeypatch) -> None:
    dummy_client = DummyMaverickClient()
    server._maverick_client = None
    monkeypatch.setattr(server, "_get_maverick_client", lambda: dummy_client)

    problem_json = json.dumps(
        {"description": "High latency on payments API", "category": "performance"}
    )
    result = asyncio.run(server.search_relevant_metrics(problem_json, limit=3))
    payload = json.loads(result)

    assert payload["query"] == problem_json
    assert payload["metrics"][0]["metric_name"] == "http_requests_total"


@pytest.mark.integration
def test_construct_promql_query_happy_path(monkeypatch) -> None:
    dummy_client = DummyMaverickClient()
    server._maverick_client = None
    monkeypatch.setattr(server, "_get_maverick_client", lambda: dummy_client)

    intent = json.dumps({"metric": "http_requests_total", "filters": {"status": "500"}})
    result = asyncio.run(server.construct_promql_query(intent))
    payload = json.loads(result)

    assert payload["success"] is True
    assert payload["query"] == "rate(http_requests_total[5m])"


@pytest.mark.integration
def test_construct_logql_query_happy_path(monkeypatch) -> None:
    dummy_client = DummyMaverickClient()
    server._maverick_client = None
    monkeypatch.setattr(server, "_get_maverick_client", lambda: dummy_client)

    intent = json.dumps(
        {
            "description": "Find errors in payments",
            "backend": "loki",
            "service": "payments",
            "patterns": [{"pattern": "error", "level": "error"}],
        }
    )
    result = asyncio.run(server.construct_logql_query(intent))
    payload = json.loads(result)

    assert payload["success"] is True
    assert payload["backend"] == "loki"
    assert payload["query"] == '{service="payments"} |~ "error"'


@pytest.mark.integration
def test_construct_splunk_query_happy_path(monkeypatch) -> None:
    dummy_client = DummyMaverickClient()
    server._maverick_client = None
    monkeypatch.setattr(server, "_get_maverick_client", lambda: dummy_client)

    intent = json.dumps(
        {
            "description": "Search for timeout errors",
            "backend": "splunk",
            "service": "payments",
            "patterns": [{"pattern": "timeout"}],
        }
    )
    result = asyncio.run(server.construct_splunk_query(intent))
    payload = json.loads(result)

    assert payload["success"] is True
    assert payload["backend"] == "splunk"
    assert payload["query"] == 'search service="payments" "timeout" | head 200'
