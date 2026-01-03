# Claude Code Development Notes

## Running Integration Tests

Run all integration tests with verbose logging:

```bash
uv run pytest -m integration -s -v --log-cli-level=INFO
```

Run a specific integration test with the following flags for more details:

```bash
uv run pytest -m integration -s -v tests/integration/maverick_engine/querygen_engine/agent/logs/test_logql_query_generator_agent_integration.py --log-cli-level=INFO
```

Flags explanation:
- `-m integration`: Run only tests marked with @pytest.mark.integration
- `-s`: Show stdout/print statements (disable capture)
- `-v`: Verbose output
- `--log-cli-level=INFO`: Show INFO level logs in console output
