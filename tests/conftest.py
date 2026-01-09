"""Root conftest.py for all tests - configures Logfire instrumentation."""

import pytest
import logfire

# Configure Logfire for all tests
logfire.configure()
logfire.instrument_pydantic_ai()


@pytest.fixture(autouse=True)
def logfire_span_for_integration_tests(request):
    """Create a Logfire span for each integration test."""
    if request.node.get_closest_marker("integration"):
        test_name = request.node.nodeid
        with logfire.span(f"test: {test_name}", test_name=test_name):
            yield
    else:
        yield
