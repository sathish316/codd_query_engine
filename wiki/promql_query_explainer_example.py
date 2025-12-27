"""
Example usage of PromQL Query Explainer Agent.

This example demonstrates how to use the PromQLQueryExplainerAgent to validate
whether a generated PromQL query semantically matches the original user intent.
"""

from maverick_engine.querygen_engine.metrics.structured_inputs import (
    MetricsQueryIntent,
    AggregationFunctionSuggestion,
)
from maverick_engine.validation_engine import (
    PromQLQueryExplainerAgent,
    SemanticValidationResult,
    SemanticValidationError,
)
from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager


def example_matching_intent():
    """Example: Query that matches the original intent."""
    print("\n" + "=" * 80)
    print("Example 1: Query MATCHES Original Intent")
    print("=" * 80)

    # Initialize the agent
    config_manager = ConfigManager()
    instructions_manager = InstructionsManager()
    explainer = PromQLQueryExplainerAgent(config_manager, instructions_manager)

    # Define the original intent
    intent = MetricsQueryIntent(
        metric="http_requests_total",
        metric_type="counter",
        filters={"status": "500"},
        window="5m",
        aggregation_suggestions=[AggregationFunctionSuggestion(function_name="rate")],
    )

    # Generated query
    generated_query = 'rate(http_requests_total{status="500"}[5m])'

    print("\nOriginal Intent:")
    print(f"  - Metric: {intent.metric}")
    print(f"  - Type: {intent.metric_type}")
    print(f"  - Filters: {intent.filters}")
    print(f"  - Window: {intent.window}")
    print("  - Suggested Aggregation: rate")

    print("\nGenerated Query:")
    print(f"  {generated_query}")

    # Validate semantic match
    try:
        result: SemanticValidationResult = explainer.validate_semantic_match(
            intent, generated_query
        )

        print(
            f"\n{'✓' if result.intent_match else '✗'} Intent Match: {result.intent_match}"
        )
        print(f"Partial Match: {result.partial_match}")
        print(f"Confidence: {result.confidence:.2%}")
        print("\nOriginal Intent Summary:")
        print(f"  {result.original_intent_summary}")
        print("\nActual Query Behavior:")
        print(f"  {result.actual_query_behavior}")
        print("\nExplanation:")
        print(f"  {result.explanation}")

    except SemanticValidationError as e:
        print(f"\n✗ Validation Error: {e}")


def example_mismatched_intent():
    """Example: Query that does NOT match the original intent."""
    print("\n" + "=" * 80)
    print("Example 2: Query DOES NOT MATCH Original Intent")
    print("=" * 80)

    config_manager = ConfigManager()
    instructions_manager = InstructionsManager()
    explainer = PromQLQueryExplainerAgent(config_manager, instructions_manager)

    # Define the original intent - expects avg_over_time for a gauge
    intent = MetricsQueryIntent(
        metric="memory_usage_bytes",
        metric_type="gauge",
        window="5m",
        aggregation_suggestions=[
            AggregationFunctionSuggestion(function_name="avg_over_time")
        ],
    )

    # Generated query - incorrectly uses rate() on a gauge
    generated_query = "rate(memory_usage_bytes[5m])"

    print("\nOriginal Intent:")
    print(f"  - Metric: {intent.metric}")
    print(f"  - Type: {intent.metric_type} (should NOT use rate!)")
    print(f"  - Window: {intent.window}")
    print("  - Suggested Aggregation: avg_over_time")

    print("\nGenerated Query (INCORRECT):")
    print(f"  {generated_query}")

    try:
        result: SemanticValidationResult = explainer.validate_semantic_match(
            intent, generated_query
        )

        print(
            f"\n{'✓' if result.intent_match else '✗'} Intent Match: {result.intent_match}"
        )
        print(f"Partial Match: {result.partial_match}")
        print(f"Confidence: {result.confidence:.2%}")
        print("\nOriginal Intent Summary:")
        print(f"  {result.original_intent_summary}")
        print("\nActual Query Behavior:")
        print(f"  {result.actual_query_behavior}")
        print("\nExplanation:")
        print(f"  {result.explanation}")

    except SemanticValidationError as e:
        print(f"\n✗ Validation Error: {e}")


def example_histogram_with_quantile():
    """Example: Histogram query with percentile calculation."""
    print("\n" + "=" * 80)
    print("Example 3: Histogram Query with 95th Percentile")
    print("=" * 80)

    config_manager = ConfigManager()
    instructions_manager = InstructionsManager()
    explainer = PromQLQueryExplainerAgent(config_manager, instructions_manager)

    intent = MetricsQueryIntent(
        metric="api_latency_seconds",
        metric_type="histogram",
        filters={"endpoint": "/users", "method": "GET"},
        window="5m",
        group_by=["instance"],
        aggregation_suggestions=[
            AggregationFunctionSuggestion(
                function_name="histogram_quantile", params={"quantile": 0.95}
            )
        ],
    )

    generated_query = """histogram_quantile(0.95,
    rate(api_latency_seconds_bucket{endpoint="/users", method="GET"}[5m])
) by (instance)"""

    print("\nOriginal Intent:")
    print(f"  - Metric: {intent.metric}")
    print(f"  - Type: {intent.metric_type}")
    print(f"  - Filters: {intent.filters}")
    print(f"  - Window: {intent.window}")
    print(f"  - Group By: {intent.group_by}")
    print("  - Aggregation: histogram_quantile (95th percentile)")

    print("\nGenerated Query:")
    print(f"  {generated_query}")

    try:
        result: SemanticValidationResult = explainer.validate_semantic_match(
            intent, generated_query
        )

        print(
            f"\n{'✓' if result.intent_match else '✗'} Intent Match: {result.intent_match}"
        )
        print(f"Partial Match: {result.partial_match}")
        print(f"Confidence: {result.confidence:.2%}")
        print("\nExplanation:")
        print(f"  {result.explanation}")

    except SemanticValidationError as e:
        print(f"\n✗ Validation Error: {e}")


def example_explain_query_only():
    """Example: Just explain a query without comparing to intent."""
    print("\n" + "=" * 80)
    print("Example 4: Explain Query (No Intent Comparison)")
    print("=" * 80)

    config_manager = ConfigManager()
    instructions_manager = InstructionsManager()
    explainer = PromQLQueryExplainerAgent(config_manager, instructions_manager)

    query = 'sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))'

    print("\nQuery to Explain:")
    print(f"  {query}")

    try:
        explanation = explainer.explain_query(query)

        print("\nQuery Explanation:")
        print(f"  {explanation}")

    except SemanticValidationError as e:
        print(f"\n✗ Explanation Error: {e}")


def example_partial_match():
    """Example: Query that partially matches the intent."""
    print("\n" + "=" * 80)
    print("Example 5: Partial Match - Minor Deviation")
    print("=" * 80)

    config_manager = ConfigManager()
    instructions_manager = InstructionsManager()
    explainer = PromQLQueryExplainerAgent(config_manager, instructions_manager)

    # Intent expects 95th percentile, but query uses 99th
    intent = MetricsQueryIntent(
        metric="api_latency_seconds",
        metric_type="histogram",
        filters={"endpoint": "/users"},
        window="5m",
        aggregation_suggestions=[
            AggregationFunctionSuggestion(
                function_name="histogram_quantile", params={"quantile": 0.95}
            )
        ],
    )

    # Query uses 99th percentile instead of 95th
    generated_query = 'histogram_quantile(0.99, rate(api_latency_seconds_bucket{endpoint="/users"}[5m]))'

    print("\nOriginal Intent:")
    print(f"  - Metric: {intent.metric}")
    print(f"  - Type: {intent.metric_type}")
    print(f"  - Filters: {intent.filters}")
    print(f"  - Window: {intent.window}")
    print("  - Expected: 95th percentile (0.95)")

    print("\nGenerated Query (Uses 99th percentile):")
    print(f"  {generated_query}")

    try:
        result: SemanticValidationResult = explainer.validate_semantic_match(
            intent, generated_query
        )

        print(
            f"\n{'✓' if result.intent_match else '✗'} Intent Match: {result.intent_match}"
        )
        print(
            f"{'✓' if result.partial_match else '✗'} Partial Match: {result.partial_match}"
        )
        print(f"Confidence: {result.confidence:.2%}")
        print("\nExplanation:")
        print(f"  {result.explanation}")

    except SemanticValidationError as e:
        print(f"\n✗ Validation Error: {e}")


def example_error_handling():
    """Example: Error handling for invalid inputs."""
    print("\n" + "=" * 80)
    print("Example 6: Error Handling")
    print("=" * 80)

    config_manager = ConfigManager()
    instructions_manager = InstructionsManager()
    explainer = PromQLQueryExplainerAgent(config_manager, instructions_manager)

    # Test 1: Empty query
    print("\nTest 1: Empty query")
    try:
        intent = MetricsQueryIntent(metric="test_metric")
        explainer.validate_semantic_match(intent, "")
    except SemanticValidationError as e:
        print(f"  ✓ Caught expected error: {e}")

    # Test 2: Intent without metric
    print("\nTest 2: Intent without metric")
    try:
        intent = MetricsQueryIntent(metric="")
        explainer.validate_semantic_match(intent, "rate(test[5m])")
    except SemanticValidationError as e:
        print(f"  ✓ Caught expected error: {e}")

    # Test 3: Empty query for explain_query
    print("\nTest 3: Empty query for explain_query")
    try:
        explainer.explain_query("")
    except SemanticValidationError as e:
        print(f"  ✓ Caught expected error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PromQL Query Explainer Agent - Usage Examples")
    print("=" * 80)

    # Run all examples
    example_matching_intent()
    example_mismatched_intent()
    example_histogram_with_quantile()
    example_explain_query_only()
    example_partial_match()
    example_error_handling()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")
