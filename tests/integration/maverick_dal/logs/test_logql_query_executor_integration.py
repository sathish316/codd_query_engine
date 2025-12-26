"""
Integration tests for LogQLQueryExecutor.

These tests verify the LogQL client works correctly against a real Loki instance.
Run these tests with: pytest -m integration

Prerequisites:
- Loki instance running at http://localhost:3100
- Test data ingested into Loki

Note: These are happy path tests that verify basic functionality.
"""

from datetime import datetime, timedelta
import pytest

from maverick_dal.logs.logql_query_executor import (
    LogQLQueryExecutor,
    LokiConfig,
)


@pytest.fixture
def loki_config():
    """Provide Loki configuration for integration tests."""
    return LokiConfig(
        base_url="http://localhost:3100",
        timeout=30
    )


@pytest.fixture
def executor(loki_config):
    """Provide a LogQLQueryExecutor instance."""
    with LogQLQueryExecutor(loki_config) as exec:
        yield exec


@pytest.mark.integration
def test_query_range(executor):
    """
    Test query_range method with a basic log query.

    Verifies that:
    - The query executes successfully
    - Returns a valid response structure
    - Status is 'success'
    - Data field is populated
    """
    # Query logs from the last hour
    end = datetime.now()
    start = end - timedelta(hours=1)

    result = executor.query_range(
        query='{job=~".+"}',  # Match any job label
        start=start,
        end=end,
        limit=10,
        direction="backward"
    )

    # Verify success
    assert result.status == "success", f"Query failed: {result.error}"
    assert result.data is not None, "Expected data in response"
    assert result.error is None, f"Unexpected error: {result.error}"

    # Verify response structure
    assert "resultType" in result.data, "Missing resultType in response"
    assert "result" in result.data, "Missing result in response"

@pytest.mark.integration
def test_get_labels(executor):
    """
    Test get_labels method to retrieve all label names.

    Verifies that:
    - The labels query executes successfully
    - Returns a list of label names
    - Status is 'success'
    - Common labels are present (if data exists)
    """
    # Query labels from the last hour
    end = datetime.now()
    start = end - timedelta(hours=1)

    result = executor.get_labels(start=start, end=end)

    # Verify success
    assert result.status == "success", f"Query failed: {result.error}"
    assert result.data is not None, "Expected data in response"
    assert result.error is None, f"Unexpected error: {result.error}"

    # Verify response is a list
    assert isinstance(result.data, list), "Expected data to be a list of labels"

    # If there's data in Loki, we should have at least some labels
    # Note: This assumes Loki has been used and has data
    if len(result.data) > 0:
        # Common Loki labels that are typically present
        # Note: Actual labels depend on your Loki instance
        assert all(isinstance(label, str) for label in result.data), \
            "All labels should be strings"


@pytest.mark.integration
def test_get_label_values(executor):
    """
    Test get_label_values method to retrieve values for a specific label.

    Verifies that:
    - The label values query executes successfully
    - Returns a list of values
    - Status is 'success'
    - Values are strings
    """
    # First, get available labels
    end = datetime.now()
    start = end - timedelta(hours=1)

    labels_result = executor.get_labels(start=start, end=end)
    assert labels_result.status == "success", "Failed to get labels for test setup"

    # If we have labels, test getting values for the first one
    if labels_result.data and len(labels_result.data) > 0:
        label_name = labels_result.data[0]

        result = executor.get_label_values(
            label_name=label_name,
            start=start,
            end=end
        )

        # Verify success
        assert result.status == "success", f"Query failed: {result.error}"
        assert result.data is not None, "Expected data in response"
        assert result.error is None, f"Unexpected error: {result.error}"

        # Verify response is a list
        assert isinstance(result.data, list), \
            f"Expected data to be a list of values for label '{label_name}'"

        # Verify all values are strings
        if len(result.data) > 0:
            assert all(isinstance(value, str) for value in result.data), \
                "All label values should be strings"
    else:
        pytest.skip("No labels available in Loki instance for testing")
