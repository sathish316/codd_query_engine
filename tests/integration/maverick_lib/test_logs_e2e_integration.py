"""End-to-end integration tests for logs operations using real providers."""

import pytest

from maverick_engine.querygen_engine.logs.structured_inputs import LogQueryIntent
from maverick_engine.logs.log_patterns import LogPattern


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logql_generation_and_validation_e2e(maverick_client):
    """
    End-to-end test: LogQL query generation and validation

    Workflow:
    1. Create LogQueryIntent for Loki backend
    2. Specify service, patterns, and log level filters
    3. Generate LogQL query using construct_logql_query()
    4. Verify query generation succeeds
    5. Verify LogQL query structure (label selectors, line filters, pipeline stages)

    This test uses:
    - Real query generator (with LLM calls) for LogQL generation
    - Real validators (with LLM calls) for LogQL validation
    """
    # Step 1 & 2: Create LogQueryIntent with patterns
    patterns = [
        LogPattern(pattern="error", level="error"),
        LogPattern(pattern="exception", level="error"),
        LogPattern(pattern="timeout", level="warn"),
    ]

    intent = LogQueryIntent(
        description="Find error and timeout logs in the payments service",
        backend="loki",
        service="payments",
        patterns=patterns,
        namespace="production",
        default_level="error",
        limit=200,
    )

    # Step 3: Generate LogQL query
    result = await maverick_client.logs.logql.construct_logql_query(intent)

    # Step 4: Verify query generation succeeded
    assert result.success is True, f"LogQL generation failed: {result.error}"
    assert result.query is not None, "Query should not be None"
    assert len(result.query) > 0, "Query should not be empty"

    # Step 5: Verify LogQL query structure
    query = result.query

    # Verify label selector (should have service label)
    assert "{" in query and "}" in query, "Query should have label selector"
    assert (
        'service="payments"' in query or "service=~" in query or "service" in query
    ), "Query should filter by service"

    # Verify line filters (LogQL uses |= or |~ for pattern matching)
    # Should contain some form of pattern matching for error/timeout
    has_line_filter = "|=" in query or "|~" in query or "|>" in query or "| " in query
    assert has_line_filter, "Query should contain LogQL line filters or pipeline stages"

    # Verify error-related pattern is mentioned
    has_error_pattern = (
        "error" in query.lower()
        or "exception" in query.lower()
        or "timeout" in query.lower()
    )
    assert has_error_pattern, (
        "Query should contain at least one of the specified patterns"
    )

    # Verify no error in result
    assert result.error is None, (
        f"Query generation should not have errors: {result.error}"
    )

    print(f"Intent: {intent.description}")
    print(f"Generated LogQL query: {query}")
    print(f"Query patterns: {[p.pattern for p in patterns]}")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipping due to PydanticAI usage limit - agent hits 50 request limit")
async def test_splunk_spl_generation_and_validation_e2e(maverick_client):
    """
    End-to-end test: Splunk SPL query generation and validation

    Workflow:
    1. Create LogQueryIntent for Splunk backend
    2. Specify search patterns and service filters
    3. Generate Splunk SPL query using construct_spl_query()
    4. Verify query generation succeeds
    5. Verify SPL query structure (search command, field filters, pipe commands)

    This test uses:
    - Real query generator (with LLM calls) for Splunk SPL generation
    - Real validators (with LLM calls) for SPL validation
    """
    # Step 1 & 2: Create LogQueryIntent for Splunk with patterns
    patterns = [
        LogPattern(pattern="timeout", level="warn"),
        LogPattern(pattern="connection refused", level="error"),
    ]

    intent = LogQueryIntent(
        description="Search for timeout and connection errors in the API gateway",
        backend="splunk",
        service="api-gateway",
        patterns=patterns,
        default_level="warn",
        limit=200,
    )

    # Step 3: Generate Splunk SPL query
    result = await maverick_client.logs.splunk.construct_spl_query(intent)

    # Step 4: Verify query generation succeeded
    assert result.success is True, f"Splunk SPL generation failed: {result.error}"
    assert result.query is not None, "Query should not be None"
    assert len(result.query) > 0, "Query should not be empty"

    # Step 5: Verify SPL query structure
    query = result.query

    # Verify search command (Splunk queries typically start with "search" or have it)
    # SPL queries can also start with index= or other commands, so be flexible
    # The key is that it should look like a valid SPL query
    assert "search" in query.lower() or "index=" in query.lower() or "|" in query, (
        "Query should be a valid SPL query with search command or index filter"
    )

    # Verify service filter (field filter in Splunk)
    assert (
        "api-gateway" in query or "api_gateway" in query or "service" in query.lower()
    ), "Query should filter by service"

    # Verify pattern search terms
    has_pattern = "timeout" in query.lower() or "connection" in query.lower()
    assert has_pattern, "Query should contain at least one of the specified patterns"

    # Verify pipe command for limiting results (typically "| head 200" or "| limit 200")
    has_limit = "| head" in query or "| limit" in query or "| tail" in query
    assert has_limit, "Query should contain pipe command to limit results"

    # Verify no error in result
    assert result.error is None, (
        f"Query generation should not have errors: {result.error}"
    )

    print(f"Intent: {intent.description}")
    print(f"Generated Splunk SPL query: {query}")
    print(f"Query patterns: {[p.pattern for p in patterns]}")
