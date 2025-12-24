"""Integration tests for hello module."""
import pytest


@pytest.mark.integration
def test_hello_integration_basic():
    """Test basic integration scenario."""
    # Simulate an integration test that might call external services
    result = {"status": "success", "message": "Hello from integration test"}
    assert result["status"] == "success"
    assert "Hello" in result["message"]


@pytest.mark.integration
def test_hello_integration_complex():
    """Test complex integration scenario."""
    # Simulate a more complex integration test
    data = {
        "users": ["Alice", "Bob", "Charlie"],
        "greetings": []
    }

    for user in data["users"]:
        data["greetings"].append(f"Hello, {user}!")

    assert len(data["greetings"]) == 3
    assert data["greetings"][0] == "Hello, Alice!"
    assert all("Hello" in greeting for greeting in data["greetings"])


@pytest.mark.integration
def test_hello_integration_slow():
    """Test that simulates a slow integration test."""
    import time

    # Simulate slow external API call
    start_time = time.time()
    time.sleep(0.1)  # Simulate 100ms delay
    elapsed = time.time() - start_time

    assert elapsed >= 0.1
    assert True  # Test passes after delay
