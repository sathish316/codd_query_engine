"""
Unit tests for PromQLSyntaxValidator.

These tests focus on syntax acceptance/rejection for common PromQL forms:
- vector selectors with label matchers
- range selectors, offsets, @ modifiers, and subqueries
- aggregations with by/without
- binary ops with vector matching and bool modifier
"""

import pytest

from codd_engine.validation_engine.metrics.syntax.promql_syntax_validator import (
    PromQLSyntaxValidator,
)


@pytest.fixture
def validator() -> PromQLSyntaxValidator:
    return PromQLSyntaxValidator()


@pytest.mark.parametrize(
    "query",
    [
        "up",
        'http_requests_total{method="GET",code=~"5.."}',
        'rate(http_requests_total{job="api"}[5m])',
        "sum by (job) (rate(http_requests_total[5m]))",
        'count_values("code", http_requests_total)',
        "topk(5, rate(http_requests_total[5m]))",
        "quantile(0.95, rate(http_requests_total[5m]))",
        "up offset 5m",
        "up offset -5m",
        "up @ 1700000000",
        "up @ start()",
        "up @ end()",
        "up[10m:1m]",
        'label_replace(up, "dst", "$1", "src", "(.*)")',
        "up and on(job) process_start_time_seconds",
        "up * on(instance) group_left(job) node_cpu_seconds_total",
        "up > bool on(job) vector(0)",
    ],
)
def test_valid_queries(validator: PromQLSyntaxValidator, query: str):
    result = validator.validate(query)
    assert result.is_valid is True, result


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "up +",
        '{job="api"',
        "rate(http_requests_total[5m)",
        "sum by (job) rate(http_requests_total[5m])",
        'http_requests_total{method="GET",}',
        "up[5m::1m]",
        "up @ start(",
    ],
)
def test_invalid_queries(validator: PromQLSyntaxValidator, query: str):
    result = validator.validate(query)
    assert result.is_valid is False
    assert result.error
