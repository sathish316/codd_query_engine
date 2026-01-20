"""Tests for log query syntax validation."""

from unittest.mock import Mock
from codd_engine.validation_engine.logs import LogQueryValidator


def test_logql_syntax_invalid():
    mock_config = Mock()
    mock_config.get.return_value = True  # Syntax validation enabled
    validator = LogQueryValidator(config_manager=mock_config)
    result = validator.validate("loki", "{invalid", "", [])
    assert not result.syntax.is_valid


def test_logql_syntax_valid():
    mock_config = Mock()
    mock_config.get.return_value = True  # Syntax validation enabled
    validator = LogQueryValidator(config_manager=mock_config)
    result = validator.validate("loki", '{service="payments"} |= "error"', "", [])
    assert result.syntax.is_valid


def test_splunk_syntax_valid():
    mock_config = Mock()
    mock_config.get.return_value = True  # Syntax validation enabled
    validator = LogQueryValidator(config_manager=mock_config)
    result = validator.validate("splunk", 'search service="payments" | head 10', "", [])
    assert result.syntax.is_valid
