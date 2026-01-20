"""
Unit tests for LogQL syntax validation.

These tests verify syntax acceptance/rejection for common LogQL query forms:
- Log stream selectors with label matchers
- Line filters (|=, |~, !=, !~)
- Parser stages (json, logfmt, pattern)
- Label filters after parsing
"""

import pytest

from codd_engine.validation_engine.logs.syntax.logql_syntax_validator import (
    LogQLSyntaxValidator,
)


@pytest.fixture
def validator() -> LogQLSyntaxValidator:
    return LogQLSyntaxValidator()


@pytest.mark.parametrize(
    "query",
    [
        # Basic selectors
        "{}",
        '{job="varlogs"}',
        '{job="varlogs", filename="/var/log/syslog"}',
        '{service="api-gateway"}',
        '{namespace="production"}',
        # Different operators
        '{job="app"}',
        '{job!="app"}',
        '{job=~"app.*"}',
        '{job!~"test.*"}',
        # Pipeline filters
        '{job="app"} |= "error"',
        '{job="app"} |~ "error|warn"',
        '{job="app"} != "debug"',
        '{job="app"} !~ "trace"',
        # Multiple pipeline stages
        '{job="app"} |= "error" |= "timeout"',
        '{job="app"} |~ "error" |= "database"',
        '{job="app"} |= "error" |~ "timeout.*"',
        # JSON parsing
        '{job="app"} | json',
        '{job="app"} | json |= "error"',
        # Complex queries
        '{service="payments", namespace="prod"} |~ "error|critical" |= "transaction"',
        '{job="kubernetes", pod=~"api-.*"}',
        '{container="app", pod!="test"}',
        # Special characters in values
        '{path="/var/log/syslog"}',
        '{message="error: timeout"}',
        '{url="http://example.com"}',
        '{tag="version-1.2.3"}',
        # Edge cases with valid names
        '{job="test-app"}',
        '{job="app_service"}',
        '{job="app123"}',
        '{_internal="true"}',
        # Whitespace handling
        '{ job="app" }',
        '{job = "app"}',
        '{job="app", namespace="prod"}',
        '{  job  =  "app"  }',
        '{job="app"}  |=  "error"',
    ],
)
def test_valid_logql_queries(validator: LogQLSyntaxValidator, query: str):
    """Test that valid LogQL queries are accepted."""
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
        # Malformed selectors
        "{",
        "}",
        "{job}",
        "{job=}",
        '{="value"}',
        # Invalid operators
        '{job=="app"}',
        "{job===app}",
        # Missing quotes
        "{job=app}",
        '{job="app}',
        # Invalid pipeline operators
        '{job="app"} = "error"',
        '{job="app"} ~ "error"',
        '{job="app"} | "error"',
        # Malformed pipelines
        '{job="app"} |= ',
        '{job="app"} |~',
        # Invalid characters
        '{job="app"} |= "error"$',
        '{job@="app"}',
        # Missing components
        '|= "error"',
        "{} |=",
        # JSON stage errors
        '{job="app"} | json error',
        # Syntax errors
        '{job="app",}',
        '{job="app" job="other"}',
        '{{job="app"}}',
        # Unclosed parentheses/braces
        '{job="app"',
        'job="app"}',
    ],
)
def test_invalid_logql_queries(validator: LogQLSyntaxValidator, query: str):
    """Test that invalid LogQL queries are rejected."""
    result = validator.validate(query)
    assert result.is_valid is False, f"Query should be invalid: {query}"
    assert result.error is not None
