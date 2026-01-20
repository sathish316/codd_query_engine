# Implementation Plan: Redis-based Metrics Metadata Store
Task ID: coddv2-me7

## Feature Overview and Goals

Implement a Redis-based store for metrics metadata that allows caching and validation of metric names per namespace. The store enables query validation by checking if metric names exist within a given namespace before executing queries.

**Goals:**
- Provide fast lookups for metric name validation
- Support namespace isolation for multi-tenant scenarios
- Enable bulk operations for populating metric catalogs

## Component Breakdown

1. **MetricsMetadataClient class** (depends on: none)
   - Main client class in `codd-dal/metrics/metrics_metadata_client.py`
   - Accepts Redis connection/client via constructor injection

2. **Redis key management** (depends on: MetricsMetadataClient)
   - Key format: `<namespace>#metric_names`
   - Private helper method `_get_key(namespace: str) -> str`

3. **Core API methods** (depends on: Redis key management)
   - `set_metric_names(namespace: str, metric_names: set[str]) -> None`
   - `get_metric_names(namespace: str) -> set[str]`
   - `add_metric_name(namespace: str, metric_name: str) -> None`
   - `is_valid_metric_name(namespace: str, metric_name: str) -> bool`

4. **Unit tests** (depends on: Core API methods)
   - Test file at `codd-dal/metrics/tests/test_metrics_metadata_client.py`

## Implementation Steps

1. **Create the MetricsMetadataClient class**
   - Add imports
   - Define class with `__init__(self, redis_client: redis.Redis)`
   - Store redis client as instance variable

2. **Implement key helper method**
   - Add `_get_key(self, namespace: str) -> str`
   - Return `f"{namespace}#metric_names"`

3. **Implement set_metric_names**
   - Delete existing key to replace all values
   - Use `SADD` to add all metric names in a single operation
   - Handle empty set case (skip SADD if empty)

4. **Implement get_metric_names**
   - Use `SMEMBERS` to retrieve all members
   - Decode bytes to strings if needed
   - Return empty set if key does not exist

5. **Implement add_metric_name**
   - Use `SADD` to add single metric name
   - Returns number of elements added (can be ignored)

6. **Implement is_valid_metric_name**
   - Use `SISMEMBER` to check membership
   - Return boolean result

7. **Create unit tests**
   - Use `fakeredis` or mock for testing
   - Test each method with various inputs
   - Test edge cases: empty namespace, empty set, non-existent keys

## Acceptance Criteria

- [ ] MetricsMetadataClient class is implemented in `codd-dal/metrics/metrics_metadata_client.py`
- [ ] `set_metric_names(namespace, metric_names)` replaces all metric names for namespace
- [ ] `get_metric_names(namespace)` returns set of all metric names (empty set if none)
- [ ] `add_metric_name(namespace, metric_name)` adds single metric to existing set
- [ ] `is_valid_metric_name(namespace, metric_name)` returns True/False for membership check
- [ ] Redis key format follows `<namespace>#metric_names` pattern
- [ ] Unit tests pass with at least 90% coverage for the new code
- [ ] Type hints are provided for all public methods

## Technical Considerations

- **Redis connection**: Accept `redis.Redis` client via constructor for flexibility (allows connection pooling, clustering)
- **Thread safety**: Redis operations are atomic; client is thread-safe
- **Error handling**: Let Redis exceptions propagate (connection errors, etc.)
- **Encoding**: Redis returns bytes by default; ensure `decode_responses=True` is used or decode manually
- **Performance**: `SISMEMBER` is O(1), `SMEMBERS` is O(n) where n is set size
- **Edge cases**:
  - Empty namespace string should be allowed and changed to "default" (caller's responsibility)
