# Claude Code Development Notes

## Running Tests

**IMPORTANT**: Always use `uv run python -m pytest` instead of `uv run pytest` to ensure pytest runs in the correct virtual environment.

### Running All Tests (excluding integration tests)
```bash
uv run python -m pytest
```

### Running Integration Tests

Run all integration tests with verbose logging:

```bash
uv run python -m pytest -m integration -s -v --log-cli-level=INFO
```

Run only LLM-based integration tests:

```bash
uv run python -m pytest -m integration_llm -s -v --log-cli-level=INFO
```

Run integration tests excluding LLM ones:

```bash
uv run python -m pytest -m "integration and not integration_llm" -s -v
```

Run a specific integration test with the following flags for more details:

```bash
uv run python -m pytest -m integration -s -v tests/integration/maverick_engine/querygen_engine/agent/logs/test_logql_query_generator_agent_integration.py --log-cli-level=INFO
```

Flags explanation:
- `-m integration`: Run only tests marked with @pytest.mark.integration
- `-m integration_llm`: Run only tests marked with @pytest.mark.integration_llm
- `-s`: Show stdout/print statements (disable capture)
- `-v`: Verbose output
- `--log-cli-level=INFO`: Show INFO level logs in console output
