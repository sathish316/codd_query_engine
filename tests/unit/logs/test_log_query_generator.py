"""Unit tests for LogQueryGenerator facade with mocked backend generators."""

import pytest
from unittest.mock import Mock, patch

from maverick_engine.logs.log_patterns import LogPattern
from maverick_engine.querygen_engine.logs.log_query_generator import LogQueryGenerator
from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.querygen_engine.logs.structured_outputs import LogQueryResult


class TestLogQueryGenerator:
    """Test suite for LogQueryGenerator facade."""

    @pytest.fixture
    def mock_loki_generator(self):
        """Mock LokiLogQLQueryGenerator."""
        return Mock()

    @pytest.fixture
    def mock_splunk_generator(self):
        """Mock SplunkSPLQueryGenerator."""
        return Mock()

    def test_generate_dispatches_to_loki_generator(
        self, mock_loki_generator, mock_splunk_generator
    ):
        """Test that LogQueryGenerator dispatches to LokiLogQLQueryGenerator for loki backend."""
        # Arrange
        intent = LogQueryIntent(
            description="timeout errors",
            backend="loki",
            patterns=[LogPattern(pattern="timeout", level="error")],
            service="payments",
        )

        expected_result = LogQueryResult(
            query='{service="payments"} |~ "timeout" | level=~"error" | limit 200',
            backend="loki",
            used_patterns=["timeout"],
            levels=["error"],
            selector='{service="payments"}',
        )

        mock_loki_generator.generate.return_value = expected_result

        # Act
        with patch(
            "maverick_engine.querygen_engine.logs.log_query_generator.facade.LokiLogQLQueryGenerator",
            return_value=mock_loki_generator,
        ):
            generator = LogQueryGenerator()
            result = generator.generate(intent)

        # Assert
        mock_loki_generator.generate.assert_called_once_with(intent)
        assert result == expected_result
        assert result.backend == "loki"
        assert '{service="payments"}' in result.query
        assert "timeout" in result.query

    def test_generate_dispatches_to_splunk_generator(
        self, mock_loki_generator, mock_splunk_generator
    ):
        """Test that LogQueryGenerator dispatches to SplunkSPLQueryGenerator for splunk backend."""
        # Arrange
        intent = LogQueryIntent(
            description="request failures",
            backend="splunk",
            patterns=[LogPattern(pattern="failed request", level="warn")],
            service="api-gateway",
        )

        expected_result = LogQueryResult(
            query='search index=* service="api-gateway" "failed request" level=warn | head 200',
            backend="splunk",
            used_patterns=["failed request"],
            levels=["warn"],
            selector='service="api-gateway"',
        )

        mock_splunk_generator.generate.return_value = expected_result

        # Act
        with patch(
            "maverick_engine.querygen_engine.logs.log_query_generator.facade.SplunkSPLQueryGenerator",
            return_value=mock_splunk_generator,
        ):
            generator = LogQueryGenerator()
            result = generator.generate(intent)

        # Assert
        mock_splunk_generator.generate.assert_called_once_with(intent)
        assert result == expected_result
        assert result.backend == "splunk"
        assert result.query.startswith("search")
        assert "api-gateway" in result.query
        assert "failed request" in result.query

    def test_generate_raises_error_for_unsupported_backend(self):
        """Test that LogQueryGenerator raises ValueError for unsupported backends."""
        # Arrange
        intent = LogQueryIntent(
            description="some query",
            backend="elasticsearch",  # Unsupported backend
            patterns=[LogPattern(pattern="error", level="error")],
            service="test",
        )

        # Act & Assert
        generator = LogQueryGenerator()
        with pytest.raises(ValueError, match="Unsupported backend: elasticsearch"):
            generator.generate(intent)
