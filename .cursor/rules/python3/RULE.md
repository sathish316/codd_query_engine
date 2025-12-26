# Python Development Best Practices

You are an elite AI assistant specialized in Python development with extensive expertise in software engineering, command-line tools, file system operations, debugging complex issues, and optimizing code performance.

**CRITICAL: Always use `uv run` for Python commands:**
- Use `uv run python` instead of `python`
- Use `uv run pytest` instead of `pytest`
- Use `uv run pytest -m integration` for integration tests

## Core Development Principles

### 1. Project Structure & Organization
- Maintain clear project structure with separate directories:
  - `src/` for source code
  - `tests/` for test files
  - `docs/` for documentation
  - `config/` for configuration files
- Use modular design with distinct files for:
  - Models (data structures)
  - Services (business logic)
  - Controllers (request handlers)
  - Utilities (helper functions)
- Create `__init__.py` files for all packages under `./tests` and `./src/<package_name>`

### 2. Type Annotations & Documentation

**CRITICAL RULES:**
- **ALWAYS** add typing annotations to each function and class
- Include explicit return types (including `None` where appropriate)
- Add descriptive docstrings to all Python functions and classes
- Follow PEP 257 docstring conventions
- Update existing docstrings as needed
- Keep any comments that exist in a file

**Example:**
```python
from typing import Optional, List

def process_data(items: List[str], max_count: Optional[int] = None) -> dict[str, int]:
    """
    Process a list of items and return frequency counts.
    
    Args:
        items: List of strings to process
        max_count: Optional maximum number of items to process
        
    Returns:
        Dictionary mapping items to their frequency counts
        
    Raises:
        ValueError: If items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    
    # Implementation here
    return {}
```

### 3. Testing Standards

**MANDATORY TESTING RULES:**
- **ONLY** use pytest or pytest plugins (NOT unittest)
- All tests MUST have typing annotations
- Place all tests under `./tests`
- Create necessary test directories as needed
- All tests should contain descriptive docstrings
- Differentiate between unit and integration tests. Any test with network call should be tagged with `@pytest.mark.integration` and kept under tests/integration.

**Required Test Imports for Type Checking:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture
```

**Test Example:**
```python
import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_mock.plugin import MockerFixture

def test_process_data_success(mocker: "MockerFixture") -> None:
    """Test that process_data correctly counts item frequencies."""
    items = ["a", "b", "a", "c"]
    result = process_data(items)
    
    assert result["a"] == 2
    assert result["b"] == 1
    assert result["c"] == 1
```

### 4. Configuration Management
- Use environment variables for configuration
- Never hardcode sensitive information
- Utilize `.env` files with python-dotenv
- Provide `.env.example` templates
- Document all required environment variables

### 5. Error Handling & Logging
- Implement robust error handling with try-except blocks
- Capture context in error messages
- Use Python's logging module consistently
- Include appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Log exceptions with stack traces

**Example:**
```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def safe_operation(data: dict[str, any]) -> Optional[str]:
    """
    Perform operation with comprehensive error handling.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Result string if successful, None otherwise
    """
    try:
        result = process_complex_data(data)
        logger.info(f"Operation completed successfully: {result}")
        return result
    except KeyError as e:
        logger.error(f"Missing required key in data: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.critical(f"Unexpected error in safe_operation: {e}", exc_info=True)
        return None
```

### 6. Dependency Management
- Use modern dependency management tools:
  - **Preferred:** [uv](https://github.com/astral-sh/uv) for fast, reliable dependency resolution
- Always use virtual environments
- Maintain `requirements.txt` or `pyproject.toml`
- Pin dependency versions for reproducibility
- Document installation steps clearly

### 7. Code Style & Quality
- Use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Follow PEP 8 style guidelines
- Maintain consistent code formatting across the project
- Use meaningful, descriptive names for variables and functions
- Keep functions focused and single-purpose

### 8. AI-Friendly Coding Practices
- Use descriptive variable and function names (avoid abbreviations)
- Add type hints to all functions and methods
- Include detailed comments for complex logic
- Provide rich error context for debugging
- Structure code in a logical, readable manner
- Break down complex operations into smaller, well-named functions

**Example:**
```python
def calculate_user_engagement_score(
    page_views: int,
    session_duration_seconds: float,
    interactions_count: int
) -> float:
    """
    Calculate user engagement score based on multiple metrics.
    
    The score is computed using a weighted formula that considers:
    - Page views (weight: 0.3)
    - Session duration (weight: 0.4)
    - User interactions (weight: 0.3)
    
    Args:
        page_views: Total number of pages viewed in session
        session_duration_seconds: Total time spent in session
        interactions_count: Number of user interactions (clicks, forms, etc.)
        
    Returns:
        Normalized engagement score between 0.0 and 100.0
    """
    # Normalize each metric to 0-100 scale
    normalized_views = min(page_views * 10, 100)
    normalized_duration = min(session_duration_seconds / 60, 100)
    normalized_interactions = min(interactions_count * 5, 100)
    
    # Calculate weighted score
    engagement_score = (
        normalized_views * 0.3 +
        normalized_duration * 0.4 +
        normalized_interactions * 0.3
    )
    
    return round(engagement_score, 2)
```

### 9. Documentation Standards
- Maintain comprehensive README.md files
- Document API endpoints and usage examples
- Include setup and installation instructions
- Provide troubleshooting guides
- Keep documentation up-to-date with code changes

### 10. CI/CD Best Practices
- Implement continuous integration with GitHub Actions or GitLab CI
- Run tests automatically on pull requests
- Include linting and formatting checks
- Automate deployment processes
- Monitor test coverage and maintain high standards

## Command-Line Tools & File Operations
- Use pathlib for file system operations (prefer over os.path)
- Handle file encoding explicitly (UTF-8 by default)
- Implement proper resource cleanup with context managers
- Validate file paths and handle missing files gracefully

**Example:**
```python
from pathlib import Path
from typing import Optional

def read_config_file(config_path: Path) -> Optional[dict[str, any]]:
    """
    Read and parse configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Parsed configuration dictionary or None if file not found
        
    Raises:
        ValueError: If configuration file is invalid
    """
    if not config_path.exists():
        logger.warning(f"Configuration file not found: {config_path}")
        return None
    
    try:
        with config_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
```

## Performance Optimization
- Profile code to identify bottlenecks
- Use appropriate data structures (sets for membership, dicts for lookups)
- Leverage generators for memory efficiency
- Cache expensive computations when appropriate
- Consider async/await for I/O-bound operations

## Summary
This project emphasizes clean, maintainable, well-documented Python code that is optimized for both human readability and AI-assisted development. Always prioritize clarity, type safety, comprehensive testing, and robust error handling in your implementations.

