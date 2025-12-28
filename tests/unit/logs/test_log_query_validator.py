"""Tests for log query syntax validation."""

from maverick_engine.validation_engine.logs import LogQueryValidator


def test_logql_syntax_invalid():
    validator = LogQueryValidator()
    result = validator.validate("loki", "{invalid", "", [])
    assert not result.syntax.is_valid


def test_logql_syntax_valid():
    validator = LogQueryValidator()
    result = validator.validate("loki", '{service="payments"} |= "error"', "", [])
    assert result.syntax.is_valid


def test_splunk_syntax_valid():
    validator = LogQueryValidator()
    result = validator.validate("splunk", 'search service="payments" | head 10', "", [])
    assert result.syntax.is_valid
