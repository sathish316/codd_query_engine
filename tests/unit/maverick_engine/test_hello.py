"""Unit tests for hello module."""


def test_hello_world():
    """Test basic hello world functionality."""
    message = "Hello, World!"
    assert message == "Hello, World!"


def test_hello_with_name():
    """Test hello with a custom name."""
    name = "Claude"
    message = f"Hello, {name}!"
    assert message == "Hello, Claude!"
    assert "Claude" in message


def test_string_operations():
    """Test basic string operations."""
    text = "hello"
    assert text.upper() == "HELLO"
    assert text.capitalize() == "Hello"
    assert len(text) == 5
