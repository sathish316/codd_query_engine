# Neo4j Cypher Grammar

This directory contains the Lark LALR grammar definition for Neo4j Cypher query language syntax validation.

## Files

- `cypher_grammar.lark` - Formal grammar definition for Cypher queries

## Coverage

The grammar supports the following Cypher features:

### Query Clauses
- **MATCH** - Pattern matching with nodes and relationships
- **OPTIONAL MATCH** - Optional pattern matching
- **WHERE** - Filtering conditions
- **RETURN** - Projection and result formatting
- **WITH** - Query chaining and intermediate results
- **CREATE** - Creating nodes and relationships
- **MERGE** - Upsert pattern (match or create)
- **DELETE/DETACH DELETE** - Removing nodes and relationships
- **SET** - Updating properties and labels
- **REMOVE** - Removing properties and labels
- **UNWIND** - List unwinding

### Patterns
- Node patterns: `(variable:Label {property: value})`
- Relationship patterns: `-[:TYPE]->`, `<-[:TYPE]-`, `-[variable:TYPE]-`
- Variable-length paths: `-[*]->`, `-[*1..3]->`
- Multiple labels: `(n:Label1:Label2)`
- Property maps with expressions

### Expressions
- Comparison operators: `=`, `<>`, `!=`, `<`, `>`, `<=`, `>=`
- Logical operators: `AND`, `OR`, `XOR`, `NOT`
- Arithmetic: `+`, `-`, `*`, `/`, `%`, `^`
- String operators: `STARTS WITH`, `ENDS WITH`, `CONTAINS`
- Null checking: `IS NULL`, `IS NOT NULL`
- List membership: `IN`

### Literals
- Numbers (integer and float)
- Strings (both single and double quotes)
- Booleans (`true`/`false`)
- Null
- Lists: `[1, 2, 3]`
- Maps: `{key: value}`

### Functions
- Aggregations: `count()`, `sum()`, `avg()`, `max()`, `min()`, `collect()`
- With `DISTINCT` modifier
- Property access: `node.property`
- Nested property access

### Result Formatting
- **ORDER BY** with ASC/DESC
- **SKIP** and **LIMIT**
- **DISTINCT**
- Aliasing with **AS**
- Projection of specific properties

### Advanced Features
- **CASE** expressions
- List comprehensions: `[x IN list WHERE condition | expression]`
- Parameters: `$paramName`
- Comments (single-line `//` and multi-line `/* */`)

## Known Limitations

1. **Standalone MATCH**: The grammar currently allows `MATCH (n)` without a RETURN clause, which is technically invalid in Cypher (though rarely encountered in practice).

2. **Function Validation**: The grammar validates function call syntax but does not verify that function names are valid Cypher built-in functions.

3. **Property Key Names**: Property keys in maps are restricted to simple identifiers, not arbitrary expressions.

## Usage

The grammar is used by `CypherSyntaxValidator` in `maverick_engine/validation_engine/graph/syntax/` for validating Cypher query syntax.

```python
from maverick_engine.validation_engine.graph.syntax import CypherSyntaxValidator

validator = CypherSyntaxValidator()
result = validator.validate("MATCH (n:Person) RETURN n")
if result.is_valid:
    print("Valid Cypher query")
else:
    print(f"Invalid: {result.error}")
```

## Testing

Unit tests are located in `tests/unit/maverick_engine/validation_engine/graph/test_cypher_syntax_validator.py`.

Run tests with:
```bash
uv run pytest tests/unit/maverick_engine/validation_engine/graph/ -v
```
