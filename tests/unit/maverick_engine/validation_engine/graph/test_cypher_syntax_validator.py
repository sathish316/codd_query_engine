"""
Unit tests for Neo4j Cypher syntax validation.

These tests verify syntax acceptance/rejection for common Cypher query forms:
- MATCH clauses with node and relationship patterns
- WHERE conditions with various operators
- RETURN projections and ordering
- CREATE, MERGE, DELETE operations
- WITH clauses for query composition
- Property access and functions
"""

import pytest

from maverick_engine.validation_engine.graph.syntax.cypher_syntax_validator import (
    CypherSyntaxValidator,
)


@pytest.fixture
def validator() -> CypherSyntaxValidator:
    return CypherSyntaxValidator()


@pytest.mark.parametrize(
    "query",
    [
        # Simple MATCH patterns
        "MATCH (n) RETURN n",
        "MATCH (n:Person) RETURN n",
        "MATCH (p:Person) RETURN p",
        "MATCH (user:User) RETURN user",
        # Node patterns with properties
        "MATCH (n {name: 'Alice'}) RETURN n",
        "MATCH (n:Person {name: 'Bob', age: 30}) RETURN n",
        "MATCH (n:User {email: 'test@example.com'}) RETURN n",
        # Relationship patterns
        "MATCH (n)-[r]->(m) RETURN n, r, m",
        "MATCH (a)-[:KNOWS]->(b) RETURN a, b",
        "MATCH (a:Person)-[:FRIEND]->(b:Person) RETURN a, b",
        "MATCH (a)-[r:WORKS_AT]->(b) RETURN a, r, b",
        # Bidirectional and undirected relationships
        "MATCH (a)<-[r]-(b) RETURN a, b",
        "MATCH (a)-[r]-(b) RETURN a, b",
        # Multiple relationships
        "MATCH (a)-[:KNOWS]->(b)-[:LIKES]->(c) RETURN a, b, c",
        "MATCH (a)-[:FRIEND]->(b), (b)-[:WORKS_AT]->(c) RETURN a, b, c",
        # Variable length paths
        "MATCH (a)-[*]->(b) RETURN a, b",
        "MATCH (a)-[*1..3]->(b) RETURN a, b",
        "MATCH (a)-[:KNOWS*2..5]->(b) RETURN a, b",
        "MATCH (a)-[r:FRIEND*]->(b) RETURN a, b",
        # WHERE clauses
        "MATCH (n:Person) WHERE n.age > 18 RETURN n",
        "MATCH (n) WHERE n.name = 'Alice' RETURN n",
        "MATCH (n) WHERE n.age >= 21 AND n.status = 'active' RETURN n",
        "MATCH (n) WHERE n.age < 65 OR n.retired = true RETURN n",
        "MATCH (n) WHERE NOT n.deleted RETURN n",
        "MATCH (n) WHERE n.name IN ['Alice', 'Bob', 'Charlie'] RETURN n",
        "MATCH (n) WHERE n.email STARTS WITH 'test' RETURN n",
        "MATCH (n) WHERE n.email ENDS WITH '@example.com' RETURN n",
        "MATCH (n) WHERE n.description CONTAINS 'important' RETURN n",
        "MATCH (n) WHERE n.value IS NULL RETURN n",
        "MATCH (n) WHERE n.value IS NOT NULL RETURN n",
        # RETURN with expressions
        "MATCH (n) RETURN n.name",
        "MATCH (n) RETURN n.name, n.age",
        "MATCH (n) RETURN n.name AS name, n.age AS age",
        "MATCH (n) RETURN DISTINCT n.type",
        "MATCH (n) RETURN n.age + 10",
        "MATCH (n) RETURN n.price * 1.1",
        "MATCH (n) RETURN n.first_name + ' ' + n.last_name",
        # Functions
        "MATCH (n) RETURN count(n)",
        "MATCH (n) RETURN count(DISTINCT n.type)",
        "MATCH (n:Person) RETURN avg(n.age)",
        "MATCH (n) RETURN sum(n.value)",
        "MATCH (n) RETURN max(n.score), min(n.score)",
        "MATCH (n) RETURN collect(n.name)",
        # ORDER BY
        "MATCH (n) RETURN n ORDER BY n.name",
        "MATCH (n) RETURN n ORDER BY n.age DESC",
        "MATCH (n) RETURN n ORDER BY n.created ASC",
        "MATCH (n) RETURN n ORDER BY n.name, n.age DESC",
        # SKIP and LIMIT
        "MATCH (n) RETURN n LIMIT 10",
        "MATCH (n) RETURN n SKIP 5",
        "MATCH (n) RETURN n SKIP 10 LIMIT 20",
        "MATCH (n) RETURN n ORDER BY n.name SKIP 5 LIMIT 10",
        # CREATE
        "CREATE (n:Person {name: 'Alice'})",
        "CREATE (a:User)-[:FOLLOWS]->(b:User)",
        "CREATE (n:Person {name: 'Bob', age: 30})",
        # MERGE
        "MERGE (n:User {id: 123})",
        "MERGE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})",
        # DELETE
        "MATCH (n:Temp) DELETE n",
        "MATCH (n:Old) DETACH DELETE n",
        # SET
        "MATCH (n:Person {name: 'Alice'}) SET n.age = 31",
        "MATCH (n) SET n.updated = true",
        "MATCH (n) SET n.name = 'New Name', n.modified = true",
        # REMOVE
        "MATCH (n) REMOVE n.temporary",
        "MATCH (n) REMOVE n:OldLabel",
        # WITH clauses
        "MATCH (n) WITH n.name AS name RETURN name",
        "MATCH (n) WITH n ORDER BY n.age LIMIT 10 RETURN n",
        "MATCH (a)-[:KNOWS]->(b) WITH a, count(b) AS friends WHERE friends > 5 RETURN a",
        # UNWIND
        "UNWIND [1, 2, 3] AS x RETURN x",
        "UNWIND $list AS item MATCH (n {id: item}) RETURN n",
        # OPTIONAL MATCH
        "OPTIONAL MATCH (n:Person) RETURN n",
        "MATCH (a:Person) OPTIONAL MATCH (a)-[:KNOWS]->(b) RETURN a, b",
        # CASE expressions
        "MATCH (n) RETURN CASE WHEN n.age < 18 THEN 'minor' ELSE 'adult' END",
        "MATCH (n) RETURN CASE n.type WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 0 END",
        # Parameters
        "MATCH (n {id: $userId}) RETURN n",
        "MATCH (n) WHERE n.age > $minAge RETURN n",
        # List literals
        "RETURN [1, 2, 3, 4, 5]",
        "RETURN ['a', 'b', 'c']",
        # Map literals
        "RETURN {name: 'Alice', age: 30}",
        "CREATE (n:Person {name: $name, age: $age})",
        # List comprehension
        "RETURN [x IN [1, 2, 3, 4, 5] WHERE x > 2]",
        "RETURN [x IN [1, 2, 3, 4, 5] | x * 2]",
        # Complex queries
        "MATCH (a:Person)-[:WORKS_AT]->(c:Company) WHERE c.name = 'Acme' RETURN a.name, c.name ORDER BY a.name",
        "MATCH (u:User) WHERE u.age > 18 AND u.verified = true RETURN u.email LIMIT 100",
        "MATCH (p:Product) WITH p.category AS cat, avg(p.price) AS avg_price RETURN cat, avg_price ORDER BY avg_price DESC",
        # Multiple labels
        "MATCH (n:Person:Employee) RETURN n",
        "CREATE (n:User:Admin {name: 'Alice'})",
        # Comments
        "MATCH (n) RETURN n // This is a comment",
        "MATCH (n) /* comment */ RETURN n",
        # Whitespace variations
        "MATCH(n)RETURN n",
        "MATCH  (n)  RETURN  n",
        "MATCH (n)\nRETURN n",
        # Case insensitivity
        "match (n) return n",
        "Match (n:Person) Return n",
        "MATCH (n:Person) return n",
    ],
)
def test_valid_cypher_queries(validator: CypherSyntaxValidator, query: str):
    """Test that valid Cypher queries are accepted."""
    result = validator.validate(query)
    assert result.is_valid is True, (
        f"Query should be valid: {query}\nError: {result.error}"
    )
    assert result.error is None


@pytest.mark.parametrize(
    "query",
    [
        # Empty/whitespace
        "",
        " ",
        "   ",
        "\t",
        # Incomplete patterns
        "MATCH",
        "MATCH (n",
        "MATCH (n))",
        "MATCH (n",
        # Missing RETURN
        "MATCH (n)",
        "MATCH (n:Person) WHERE n.age > 18",
        # Invalid relationship syntax
        "MATCH (a)--[r]->(b) RETURN a",  # Double dash with brackets
        "MATCH (a)-[r](b) RETURN a",  # Missing arrow
        "MATCH (a)>[r]-(b) RETURN a",  # Arrow in wrong position
        # Invalid property syntax
        "MATCH (n {name}) RETURN n",  # Missing value
        "MATCH (n {name:}) RETURN n",  # Missing value
        "MATCH (n {:value}) RETURN n",  # Missing key
        # Invalid WHERE syntax
        "MATCH (n) WHERE RETURN n",  # Missing condition
        "MATCH (n) WHERE n. RETURN n",  # Incomplete property access
        # Invalid operators
        "MATCH (n) WHERE n.age >> 18 RETURN n",
        "MATCH (n) WHERE n.name === 'Alice' RETURN n",
        # Mismatched parentheses
        "MATCH ((n) RETURN n",
        "MATCH (n)) RETURN n",
        # Invalid keywords
        "FIND (n) RETURN n",
        "MATCH (n) SELECT n",
        "MATCH (n) RETURN n ORDERBY n.name",  # Missing space
        # Invalid label syntax
        "MATCH (n::Person) RETURN n",  # Double colon
        "MATCH (n:) RETURN n",  # Empty label
        # Invalid variable names
        "MATCH (123) RETURN n",  # Starting with number
        "MATCH ($n) RETURN n",  # Dollar sign in variable
        # Missing commas
        "MATCH (n) RETURN n.name n.age",
        "MATCH (a) (b) RETURN a, b",
        # Invalid function calls
        "MATCH (n) RETURN count()",  # Missing argument
        "MATCH (n) RETURN count",  # Missing parentheses
        # Invalid LIMIT/SKIP
        "MATCH (n) RETURN n LIMIT",
        "MATCH (n) RETURN n SKIP",
        "MATCH (n) RETURN n LIMIT abc",  # Non-numeric
        # Invalid SET syntax
        "MATCH (n) SET RETURN n",
        "MATCH (n) SET n. = 10 RETURN n",
        # Trailing operators
        "MATCH (n) WHERE n.age > RETURN n",
        "MATCH (n) RETURN n.age +",
        # Invalid CASE
        "MATCH (n) RETURN CASE WHEN THEN 'value' END",  # Missing condition
        "MATCH (n) RETURN CASE WHEN true 'value' END",  # Missing THEN
        # Unclosed strings
        "MATCH (n {name: 'Alice}) RETURN n",
        'MATCH (n {name: "Alice) RETURN n',
        # Invalid list comprehension
        "RETURN [x IN WHERE x > 2]",  # Missing list
        "RETURN [IN [1,2,3] WHERE x > 2]",  # Missing variable
    ],
)
def test_invalid_cypher_queries(validator: CypherSyntaxValidator, query: str):
    """Test that invalid Cypher queries are rejected."""
    result = validator.validate(query)
    assert result.is_valid is False, f"Query should be invalid: {query}"
    assert result.error is not None
    assert isinstance(result.error, str)
