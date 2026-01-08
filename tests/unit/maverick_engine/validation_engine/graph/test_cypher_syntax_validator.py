"""
Unit tests for Cypher syntax validation using property-based testing.

These tests verify syntax acceptance/rejection for common Cypher query forms:
- Node patterns with labels and properties
- Relationship patterns with types and directions
- MATCH, RETURN, WHERE clauses
- CREATE, DELETE, SET operations
- Property access and filtering

Uses Hypothesis for property-based testing to generate varied test cases.
"""

import pytest
from hypothesis import given, strategies as st

from maverick_engine.validation_engine.graph.syntax.cypher_syntax_validator import (
    CypherSyntaxValidator,
)


@pytest.fixture
def validator() -> CypherSyntaxValidator:
    """Create a Cypher syntax validator instance."""
    return CypherSyntaxValidator()


# ============================================================================
# POSITIVE TEST CASES - Valid Cypher Syntax
# ============================================================================


@given(
    label=st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=65, max_codepoint=122
        ),
        min_size=1,
        max_size=20,
    ).filter(lambda x: x[0].isalpha())
)
def test_valid_simple_node_match_with_label(
    validator: CypherSyntaxValidator, label: str
):
    """
    Test Case 1: Simple node pattern with label.

    Validates that basic MATCH queries with node labels are accepted.
    Example: MATCH (n:Person) RETURN n

    Property-based test that generates valid label names (alphanumeric, starting with letter).
    """
    query = f"MATCH (n:{label}) RETURN n"
    result = validator.validate(query)
    assert result.is_valid is True, f"Query should be valid: {query}, Error: {result.error}"
    assert result.error is None


@given(
    label=st.sampled_from(["Person", "User", "Product", "Company", "Order"]),
    property_name=st.sampled_from(["name", "age", "email", "id", "title"]),
    property_value=st.one_of(
        st.integers(min_value=1, max_value=1000),
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=65, max_codepoint=122
            ),
            min_size=1,
            max_size=20,
        ),
    ),
)
def test_valid_node_match_with_properties(
    validator: CypherSyntaxValidator, label: str, property_name: str, property_value
):
    """
    Test Case 2: Node pattern with inline properties.

    Validates that MATCH queries with property filters in node patterns are accepted.
    Example: MATCH (n:Person {name: "Alice"}) RETURN n

    Property-based test that generates various property names and values (strings/integers).
    """
    if isinstance(property_value, str):
        query = f'MATCH (n:{label} {{{property_name}: "{property_value}"}}) RETURN n'
    else:
        query = f"MATCH (n:{label} {{{property_name}: {property_value}}}) RETURN n"

    result = validator.validate(query)
    assert result.is_valid is True, f"Query should be valid: {query}, Error: {result.error}"
    assert result.error is None


@given(
    source_label=st.sampled_from(["Person", "User", "Employee"]),
    target_label=st.sampled_from(["Company", "Department", "Organization"]),
    relationship=st.sampled_from(["WORKS_AT", "MANAGES", "BELONGS_TO", "KNOWS"]),
)
def test_valid_relationship_pattern(
    validator: CypherSyntaxValidator, source_label: str, target_label: str, relationship: str
):
    """
    Test Case 3: Relationship patterns with direction.

    Validates that MATCH queries with directed relationships are accepted.
    Example: MATCH (p:Person)-[:WORKS_AT]->(c:Company) RETURN p, c

    Property-based test generating various label and relationship type combinations.
    """
    query = f"MATCH (a:{source_label})-[:{relationship}]->(b:{target_label}) RETURN a, b"
    result = validator.validate(query)
    assert result.is_valid is True, f"Query should be valid: {query}, Error: {result.error}"
    assert result.error is None


@given(
    label=st.sampled_from(["Person", "User", "Product"]),
    property_name=st.sampled_from(["age", "price", "quantity", "rating"]),
    threshold=st.integers(min_value=1, max_value=100),
    operator=st.sampled_from([">", "<", ">=", "<=", "="]),
)
def test_valid_match_with_where_clause(
    validator: CypherSyntaxValidator, label: str, property_name: str, threshold: int, operator: str
):
    """
    Test Case 4: MATCH with WHERE clause filtering.

    Validates that queries with WHERE clauses for property comparisons are accepted.
    Example: MATCH (n:Person) WHERE n.age > 30 RETURN n

    Property-based test generating various comparison operators and threshold values.
    """
    query = f"MATCH (n:{label}) WHERE n.{property_name} {operator} {threshold} RETURN n"
    result = validator.validate(query)
    assert result.is_valid is True, f"Query should be valid: {query}, Error: {result.error}"
    assert result.error is None


@given(
    label=st.sampled_from(["Person", "User", "Account"]),
    name_value=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll"), min_codepoint=65, max_codepoint=122),
        min_size=3,
        max_size=15,
    ),
    age_value=st.integers(min_value=18, max_value=100),
)
def test_valid_create_node_with_properties(
    validator: CypherSyntaxValidator, label: str, name_value: str, age_value: int
):
    """
    Test Case 5: CREATE statement with node properties.

    Validates that CREATE queries for nodes with multiple properties are accepted.
    Example: CREATE (n:Person {name: "Alice", age: 30})

    Property-based test generating various property combinations for node creation.
    """
    query = f'CREATE (n:{label} {{name: "{name_value}", age: {age_value}}})'
    result = validator.validate(query)
    assert result.is_valid is True, f"Query should be valid: {query}, Error: {result.error}"
    assert result.error is None


# ============================================================================
# NEGATIVE TEST CASES - Invalid Cypher Syntax
# ============================================================================


@given(
    invalid_pattern=st.sampled_from([
        "MATCH (n:",  # Unclosed node pattern - missing label and closing paren
        "MATCH (n:)",  # Empty label
        "MATCH n:Label",  # Missing parentheses around node
        "MATCH (:Label",  # Unclosed parentheses
        "MATCH Label)",  # Missing opening parenthesis and colon
    ])
)
def test_invalid_malformed_node_patterns(
    validator: CypherSyntaxValidator, invalid_pattern: str
):
    """
    Test Case 6: Malformed node patterns.

    Validates that incomplete or malformed node patterns are rejected.
    Tests various syntax errors in node definitions like:
    - Unclosed parentheses
    - Missing colons before labels
    - Empty labels
    - Missing parentheses entirely

    Property-based test sampling from known malformed patterns.
    """
    result = validator.validate(invalid_pattern)
    assert result.is_valid is False, f"Query should be invalid: {invalid_pattern}"
    assert result.error is not None


@given(
    invalid_relationship=st.sampled_from([
        "MATCH (a)-[:KNOWS->(b)",  # Missing closing bracket
        "MATCH (a)-[KNOWS]->(b)",  # Missing colon before relationship type
        "MATCH (a)-->(b)",  # Missing relationship brackets
        "MATCH (a)-[:]->(b)",  # Empty relationship type
        "MATCH (a)[:KNOWS](b)",  # Missing dashes around relationship
    ])
)
def test_invalid_malformed_relationship_patterns(
    validator: CypherSyntaxValidator, invalid_relationship: str
):
    """
    Test Case 7: Malformed relationship patterns.

    Validates that incorrect relationship syntax is rejected.
    Tests various relationship syntax errors like:
    - Missing brackets around relationship types
    - Missing colons before relationship names
    - Empty relationship types
    - Incorrect arrow syntax

    Property-based test sampling from known malformed relationship patterns.
    """
    result = validator.validate(invalid_relationship)
    assert result.is_valid is False, f"Query should be invalid: {invalid_relationship}"
    assert result.error is not None


@given(
    incomplete_query=st.sampled_from([
        "MATCH (n:Person)",  # Missing RETURN clause
        "WHERE n.age > 30",  # WHERE without MATCH
        "RETURN n",  # RETURN without MATCH
        "(n:Person) RETURN n",  # Missing MATCH keyword
        "MATCH (n:Person) WHERE",  # Incomplete WHERE clause
    ])
)
def test_invalid_incomplete_query_structure(
    validator: CypherSyntaxValidator, incomplete_query: str
):
    """
    Test Case 8: Incomplete query structures.

    Validates that queries missing required clauses are rejected.
    Tests structural errors like:
    - MATCH without RETURN
    - WHERE without MATCH
    - Missing keywords
    - Incomplete clause definitions

    Property-based test sampling from various incomplete query patterns.
    """
    result = validator.validate(incomplete_query)
    assert result.is_valid is False, f"Query should be invalid: {incomplete_query}"
    assert result.error is not None


@given(
    invalid_property=st.sampled_from([
        'MATCH (n:Person {name: }) RETURN n',  # Missing property value
        'MATCH (n:Person {: "Alice"}) RETURN n',  # Missing property name
        'MATCH (n:Person {name "Alice"}) RETURN n',  # Missing colon in property
        "MATCH (n:Person {name: 'Alice'}) RETURN n",  # Single quotes instead of double
        "MATCH (n:Person {name: Alice}) RETURN n",  # Unquoted string value
    ])
)
def test_invalid_property_syntax(
    validator: CypherSyntaxValidator, invalid_property: str
):
    """
    Test Case 9: Invalid property syntax.

    Validates that malformed property definitions are rejected.
    Tests property-related errors like:
    - Missing property names or values
    - Missing colons in property definitions
    - Incorrect quote types (single vs double)
    - Unquoted string values

    Property-based test sampling from various property syntax errors.
    """
    result = validator.validate(invalid_property)
    assert result.is_valid is False, f"Query should be invalid: {invalid_property}"
    assert result.error is not None


@given(
    empty_or_whitespace=st.sampled_from([
        "",  # Empty string
        " ",  # Single space
        "   ",  # Multiple spaces
        "\t",  # Tab character
        "\n",  # Newline
        "  \t\n  ",  # Mixed whitespace
    ])
)
def test_invalid_empty_and_whitespace_queries(
    validator: CypherSyntaxValidator, empty_or_whitespace: str
):
    """
    Test Case 10: Empty and whitespace-only queries.

    Validates that empty or whitespace-only input is rejected.
    Tests edge cases with:
    - Empty strings
    - Space-only strings
    - Tab characters
    - Newlines
    - Mixed whitespace combinations

    Property-based test sampling from various whitespace patterns.
    """
    result = validator.validate(empty_or_whitespace)
    assert result.is_valid is False, f"Query should be invalid: '{empty_or_whitespace}'"
    assert result.error is not None
