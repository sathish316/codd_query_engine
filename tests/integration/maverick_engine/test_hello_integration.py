"""Integration tests for hello module."""

import pytest


@pytest.mark.integration
def test_hello_integration():
    """Test basic integration scenario."""
    # Simulate an integration test that might call external services
    result = {"status": "success", "message": "Hello from integration test"}
    assert result["status"] == "success"
    assert "Hello" in result["message"]
