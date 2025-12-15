# Implementation Plan: Schema Validator via Redis Metadata Store

## 1. Feature Overview & Goals
Implement a schema validator in `maverick-engine/validation_engine` that guarantees every metric referenced in an expression exists in the caller’s namespace. Metric names must be extracted by a PydanticAI agent backed by an OpenAI model, normalized, and cross-checked against the Redis-backed `MetricsMetadataClient`. The validator should expose a simple API (`SchemaValidator.validate`) returning structured success/failure details that upstream services can use for gating query execution.

## 2. Component Breakdown & Dependencies
1. **LLM settings & wiring (`maverick-engine/config/llm_settings.py`)** – Centralizes OpenAI credentials, retry, and confidence thresholds. Needed by the parser.
2. **PydanticAI parser (`maverick-engine/validation_engine/pydantic_metric_parser.py`)** – Implements the `MetricExpressionParser` protocol using `pydantic_ai.Agent` + `OpenAIModel`, including normalization, dedupe, and retry logic.
3. **Schema validator (`maverick-engine/validation_engine/schema_validator.py`)** – Orchestrates parsing, delegates membership checks to `MetricsMetadataClient`, applies bulk vs. per-metric validation strategies, and emits `SchemaValidationResult` objects.
4. **Redis metadata client (`maverick-dal/metrics/metrics_metadata_client.py`)** – Already provides namespace-scoped metric sets; consumed by the validator.
5. **Test suites (`maverick-engine/tests/validation_engine/test_schema_validator.py`, `.../test_pydantic_metric_parser.py`)** – Cover parser normalization/error paths, validator happy-path/failure scenarios, and Redis integration via `fakeredis` or mocks.

## 3. Implementation Steps
1. **Finalize LLM settings surface**
   - Ensure `LLMSettings` exposes `has_api_key` guard and sane defaults (already in file) and document required env vars in README if needed.
2. **Build PydanticAI parser**
   - Create `MetricExtractionResponse` Pydantic model with validators (lowercase, strip, dedupe, confidence clamp).
   - Implement `PydanticAIMetricExpressionParser` with cached agent creation, retry/backoff (`_extract_with_retry`), and regex filtering (`VALID_METRIC_NAME_PATTERN`).
   - Provide informative error classification (auth, rate-limit, timeout) and allow dependency injection of a stub agent for tests.
3. **Implement schema validator**
   - Define `MetricExpressionParseError`, `SchemaValidationResult`, and `MetricExpressionParser` protocol.
   - `SchemaValidator.validate` should short-circuit on empty expressions, None namespaces, and zero metrics.
   - Use `bulk_fetch_threshold` to decide between `get_metric_names` (bulk) and `is_valid_metric_name` (per metric); sort invalid metrics for deterministic output.
   - Add `with_default_parser` factory that loads `LLMSettings` and parser module via `importlib` to avoid circular imports.
4. **Test coverage**
   - Parser tests: stub agent success, invalid names filtered, dedupe, low confidence warning, retry/error wrapping.
   - Validator tests: happy path, missing metrics, parser exceptions, empty expression shortcuts, bulk vs. individual lookups, namespace isolation, sorted invalid outputs.
   - Integration-style test using `fakeredis` + real `MetricsMetadataClient` to verify Redis wiring end-to-end.

## 4. Acceptance Criteria
- `SchemaValidator.validate(namespace, expression)` returns `SchemaValidationResult` with accurate `is_valid`, `invalid_metrics`, and contextual error messages.
- PydanticAI parser extracts metric identifiers (lowercase, dot/underscore allowed) and filters malformed tokens before returning a `set[str]`.
- Redis metadata client is invoked via `get_metric_names` when requested metrics count ≥ threshold, otherwise via `is_valid_metric_name` per metric.
- `with_default_parser` factory loads LLM settings from `maverick-engine/config/llm_settings.py`, instantiates `PydanticAIMetricExpressionParser`, and logs selected model.
- Parser gracefully handles missing API keys, OpenAI timeouts, and rate limits by raising `MetricExpressionParseError` with actionable messages.
- Unit tests in `maverick-engine/tests/validation_engine` cover: parser normalization/error paths, validator success/failure/bulk logic, and Redis-backed integration flow.

## 5. Technical Considerations & Edge Cases
- **Environment setup**: enforce `OPENAI_API_KEY` presence before issuing OpenAI calls; allow injecting stub agents for offline tests.
- **Performance**: Avoid redundant Redis calls by deduping metric names before lookup; bulk fetch prevents O(n) round-trips when expressions reference many metrics.
- **Thread safety**: Parser caches the `Agent` instance; ensure it’s reused safely (PydanticAI agents are stateless between `run_sync` calls).
- **Error messaging**: Include namespace and truncated invalid metric list (default 5) in error strings for better observability.
- **Edge inputs**: Support empty/whitespace expressions, None namespace (should error), unicode metric names (Redis returns UTF-8 strings), and namespaces with special characters.
- **Testing strategy**: Use `fakeredis.FakeStrictRedis(decode_responses=True)` for integration tests; stub agent to avoid real OpenAI usage in CI.
