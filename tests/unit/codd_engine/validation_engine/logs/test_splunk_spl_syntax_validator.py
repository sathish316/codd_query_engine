"""
Unit tests for Splunk SPL syntax validation.

These tests verify syntax acceptance/rejection for common Splunk SPL query forms:
- Basic search commands with terms and phrases
- Field expressions with various operators
- Logical operators (AND, OR)
- Pipe stages (head, stats, table, sort, etc.)
- Grouping with parentheses
"""

import pytest

from codd_engine.validation_engine.logs.syntax.splunk_syntax_validator import (
    SplunkSPLSyntaxValidator,
)


@pytest.fixture
def validator() -> SplunkSPLSyntaxValidator:
    return SplunkSPLSyntaxValidator()


@pytest.mark.parametrize(
    "query",
    [
        # Basic search
        "search",
        'search "error"',
        'search "error message"',
        # Field expressions
        "search status=200",
        "search status!=404",
        "search count>100",
        "search count<50",
        "search count>=100",
        "search count<=50",
        # Multiple field expressions
        "search status=200 method=GET",
        'search service="api-gateway" status=500',
        # Pipe stages
        "search status=500 | head 10",
        "search status=500 | head",
        "search | stats count",
        "search | table host",
        "search | sort timestamp",
        "search | fields host",
        "search | timechart count",
        # Multiple pipe stages
        "search status=500 | head 100 | stats count",
        "search status=500 | fields host | head 20",
        # Parentheses grouping
        "search (status=500)",
        # Complex queries
        'search service="payments" status=500 | stats count | head 10',
        "search host=server-01",
        # Special field names
        "search _time>0",
        "search host=server-01",
        'search source="/var/log/syslog"',
        "search sourcetype=access_log",
        # Field names with special chars
        "search app_name=test",
        "search log-level=error",
        "search host.name=server01",
        "search _internal=true",
        # Quoted phrases with special characters
        'search "error: connection timeout"',
        'search "failed - retry exhausted"',
        'search message="HTTP/1.1 500"',
        'search "exception @ line 123"',
        # Numeric values
        "search count=100",
        "search status=200",
        "search _time>1234567890",
        "search port=8080",
        # Whitespace variations
        "search   status=200   method=GET",
        # Common Splunk patterns
        "search status=500 | stats count",
        # Logical operators with explicit AND/OR
        'search "timeout" AND level="error"',
        'search "timeout" OR level="error"',
        'search status=500 AND method=GET',
        'search status=500 OR status=502',
        # Parentheses with logical operators
        'search ("timeout" AND level="error")',
        'search (status=500 AND method=GET)',
        'search (status=500 OR status=502)',
        # Nested parentheses with logical operators
        'search service="api-gateway" (("timeout" AND level="error") OR ("connection refused" AND level="info"))',
        'search ((status=500 AND method=GET) OR (status=502 AND method=POST))',
        # Complex queries with mixed operators and parentheses
        'search service="api-gateway" ( "timeout" level="error" ) OR ( "connection refused" level="info" ) | head 100',
        'search service="api-gateway" ("timeout" AND level="error")',
        'search host=server-01 (status=500 OR status=502) method=GET',
        # Multiple levels of nesting
        'search (((status=500)))',
        'search ((status=500 OR status=502) AND (method=GET OR method=POST))',
        # Mixed implicit and explicit AND
        'search service="api" status=500 AND method=GET',
        'search "error" "timeout" AND level="critical"',
    ],
)
def test_valid_splunk_queries(validator: SplunkSPLSyntaxValidator, query: str):
    """Test that valid Splunk SPL queries are accepted."""
    result = validator.validate(query)
    assert result.is_valid is True, (
        f"Query should be valid: {query}, Error: {result.error}"
    )
    assert result.error is None


@pytest.mark.parametrize(
    "query",
    [
        # Empty/whitespace
        "",
        " ",
        "   ",
        "\t",
        # Missing search keyword
        "status=200",
        "| head 10",
        "error timeout",
        "index=main error",
        # Invalid operators
        "search status==200",
        "search count===100",
        "search status<>404",
        # Malformed expressions
        "search status=",
        "search =200",
        "search status 200",
        # Unclosed quotes
        'search "error',
        'search error"',
        # Invalid parentheses
        "search (status=500",
        "search status=500)",
        "search ((status=500)",
        # Invalid pipe syntax
        "search error |",
        "search | | head 10",
        "search error ||  head 10",
        # Invalid logical operators
        "search status=500 ANDALSO status=502",
        "search error && timeout",
        "search error || warning",
        # Special characters
        "search status@200",
        "search status=200;",
        "search status=200,",
        # Invalid field names
        "search 123field=value",
    ],
)
def test_invalid_splunk_queries(validator: SplunkSPLSyntaxValidator, query: str):
    """Test that invalid Splunk SPL queries are rejected."""
    result = validator.validate(query)
    assert result.is_valid is False, f"Query should be invalid: {query}"
    assert result.error is not None
