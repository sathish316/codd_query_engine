from maverick_engine.validation_engine.metrics.structured_outputs import (
    MetricExtractionResponse,
)
from maverick_engine.validation_engine.metrics.schema.structured_outputs import (
    SchemaValidationResult,
)


class TestMetricExtractionResponse:
    """Tests for MetricExtractionResponse."""

    def test_normalize_metric_names_lowercase(self):
        """Test that metric names are normalized to lowercase."""
        response = MetricExtractionResponse(
            metric_names=["CPU.Usage", "MEMORY.TOTAL", "Disk.IO"],
        )
        assert response.metric_names == ["cpu.usage", "memory.total", "disk.io"]

    def test_normalize_metric_names_strip_whitespace(self):
        """Test that whitespace is stripped from metric names."""
        response = MetricExtractionResponse(
            metric_names=["  cpu.usage  ", "\tmemory.total\n", " disk.io"],
        )
        assert response.metric_names == ["cpu.usage", "memory.total", "disk.io"]

    def test_normalize_metric_names_remove_empty(self):
        """Test that empty strings are removed from metric names."""
        response = MetricExtractionResponse(
            metric_names=["cpu.usage", "", "  ", "memory.total", None],
        )
        # Note: None gets filtered out in normalize_metric_names
        assert "cpu.usage" in response.metric_names
        assert "memory.total" in response.metric_names
        assert "" not in response.metric_names

    def test_dedupe_metric_names(self):
        """Test that duplicate metric names are removed."""
        response = MetricExtractionResponse(
            metric_names=["cpu.usage", "memory.total", "cpu.usage", "memory.total"],
        )
        assert response.metric_names == ["cpu.usage", "memory.total"]

    def test_dedupe_preserves_order(self):
        """Test that deduplication preserves first occurrence order."""
        response = MetricExtractionResponse(
            metric_names=["zebra", "alpha", "zebra", "beta", "alpha"],
        )
        assert response.metric_names == ["zebra", "alpha", "beta"]

    def test_metric_names_non_list_returns_empty(self):
        """Test that non-list metric_names returns empty list."""
        response = MetricExtractionResponse(
            metric_names="not a list",
        )
        assert response.metric_names == []


class TestSchemaValidationResult:
    """Tests for SchemaValidationResult dataclass."""

    def test_success_result(self):
        """Test creating a success result."""
        result = SchemaValidationResult.success()
        assert result.is_valid is True
        assert result.invalid_metrics == []
        assert result.error is None

    def test_failure_result(self):
        """Test creating a failure result with invalid metrics."""
        invalid = ["metric1", "metric2"]
        result = SchemaValidationResult.failure(invalid, "test_namespace")
        assert result.is_valid is False
        assert result.invalid_metrics == invalid
        assert "metric1" in result.error
        assert "metric2" in result.error

    def test_parse_error_result(self):
        """Test creating a parse error result."""
        result = SchemaValidationResult.parse_error("Invalid syntax")
        assert result.is_valid is False
        assert result.invalid_metrics == []
        assert "Expression parse error" in result.error
        assert "Invalid syntax" in result.error

    def test_error_message_truncation(self):
        """Test that error message truncates long metric lists."""
        invalid = [f"metric{i}" for i in range(10)]
        result = SchemaValidationResult.failure(invalid, "ns")
        # Should show first 5 and indicate more
        assert "10 invalid metrics" in result.error
        assert "and 5 more" in result.error
