# Contributing to DocumentDB Functional Tests

Thank you for your interest in contributing to the DocumentDB Functional Tests! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Access to a DocumentDB or MongoDB instance for testing

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/functional-tests.git
   cd functional-tests
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Writing Tests

For comprehensive testing guidance, see our detailed documentation:

- **[Test Format Guide](docs/testing/TEST_FORMAT.md)** - Test structure, naming, assertions, and tags
- **[Test Coverage Guide](docs/testing/TEST_COVERAGE.md)** - Coverage strategies and edge case testing
- **[Folder Structure Guide](docs/testing/FOLDER_STRUCTURE.md)** - Where to put tests with decision tree

### Test File Organization

- Place tests in the appropriate directory based on the operation being tested
- Use descriptive file names: `test_<feature>.py`
- Group related tests in the same file
- See [Folder Structure Guide](docs/testing/FOLDER_STRUCTURE.md) for detailed organization rules

### Test Structure

Every test should follow this structure:

```python
import pytest
from tests.common.assertions import assert_document_match

@pytest.mark.<operation>  # Required: e.g., find, insert, aggregate
@pytest.mark.<feature>    # Optional: e.g., rbac, decimal128
def test_descriptive_name(collection):
    """
    Clear description of what this test validates.
    
    This should explain:
    - What feature/behavior is being tested
    - Expected outcome
    - Any special conditions or edge cases
    """
    # Arrange - Insert test data
    collection.insert_one({"a": 1, "b": 2})
    
    # Execute the operation being tested, use runCommand format
    execute_command(collection, {"find": collection.name, "filter": {"a": 1}})
    
    # Assert expected behavior, don't use plain assert for consistent failure log format
    # Assert whole output when possible, to catch all unexpected regression
    expected = [{"_id": 0, "a": 1, "b": 2}]
    assertSuccess(result, expected)
```

### Test Case Guidelines

- Each test function defines one test case
- One assertion per test function
- Use execute_command for all MongoDB operations

### Naming Conventions

- **Test functions**: `test_<what_is_being_tested>`
  - Good: `test_find_with_gt_operator`
  - Bad: `test_1`, `test_query`

- **Test files**: `test_<feature_area>.py`
  - Good: `test_query_operators.py`
  - Bad: `tests.py`, `test.py`

### Required Tags

Every test MUST have at least one horizontal tag (operation):
- `@pytest.mark.find`
- `@pytest.mark.insert`
- `@pytest.mark.update`
- `@pytest.mark.delete`
- `@pytest.mark.aggregate`
- `@pytest.mark.index`
- `@pytest.mark.admin`
- `@pytest.mark.collection_mgmt`

### Optional Tags

Add vertical tags for cross-cutting features:
- `@pytest.mark.rbac` - Role-based access control
- `@pytest.mark.decimal128` - Decimal128 data type
- `@pytest.mark.collation` - Collation/sorting
- `@pytest.mark.transactions` - Transactions
- `@pytest.mark.geospatial` - Geospatial queries
- `@pytest.mark.text_search` - Text search
- `@pytest.mark.validation` - Schema validation
- `@pytest.mark.ttl` - Time-to-live indexes

Add special tags when appropriate:
- `@pytest.mark.smoke` - Quick smoke tests
- `@pytest.mark.slow` - Tests taking > 5 seconds

### Using Fixtures

The framework provides three main fixtures:

1. **engine_client**: Raw MongoDB client
   ```python
   def test_with_client(engine_client):
       db = engine_client.test_db
       collection = db.test_collection
       # ... test code
   ```

2. **database_client**: Database with automatic cleanup
   ```python
   def test_with_database(database_client):
       collection = database_client.my_collection
       # ... test code
       # Database automatically dropped after test
   ```

3. **collection**: Empty collection with automatic cleanup
   ```python
   def test_with_collection(collection):
       # Arrange - Insert test data
       collection.insert_one({"name": "Alice"})
       
       # Act - Execute operation
       result = execute_command(collection, {"find": collection.name, "filter": {"name": "Alice"}})
       
       # Assert - Verify results
       assertSuccess(result, {"name": "Alice"})
       # Collection automatically dropped after test
   ```

### Custom Assertions

Use the provided assertion helpers for common scenarios:

```python
from tests.common.assertions import (
    assert_document_match,
    assert_documents_match,
    assert_field_exists,
    assert_field_not_exists,
    assert_count
)

# Good: Use custom assertions
assert_document_match(actual, expected, ignore_id=True)
assert_count(collection, {"status": "active"}, 5)

# Avoid: Manual comparison that's verbose
actual_doc = {k: v for k, v in actual.items() if k != "_id"}
expected_doc = {k: v for k, v in expected.items() if k != "_id"}
assert actual_doc == expected_doc
```

## Code Quality

### Before Submitting

Run these commands to ensure code quality:

```bash
# Format code
black .

# Sort imports
isort .

# Run linter
flake8

# Type checking (optional but recommended)
mypy .

# Run tests
pytest
```

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable names
- Add docstrings to test functions
- Keep test functions focused on a single behavior
- Avoid complex logic in tests

## Testing Your Changes

### Run Tests Locally

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/find/test_basic_queries.py

# Run specific test
pytest tests/find/test_basic_queries.py::test_find_all_documents

# Run with your changes only
pytest -m "your_new_tag"
```

### Test Against Multiple Engines

To test against multiple engines, run pytest separately for each engine:

```bash
# Test against DocumentDB
pytest --connection-string mongodb://localhost:27017 --engine-name documentdb

# Test against MongoDB
pytest --connection-string mongodb://mongo:27017 --engine-name mongodb
```

## Submitting Changes

### Pull Request Process

1. Ensure your code follows the style guidelines
2. Add tests for new functionality
3. Update documentation if needed
4. Commit with clear, descriptive messages:
   ```bash
   git commit -m "Add tests for $group stage with $avg operator"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request on GitHub

### Pull Request Guidelines

Your PR should:
- Have a clear title describing the change
- Include a description explaining:
  - What the change does
  - Why it's needed
  - How to test it
- Reference any related issues
- Pass all CI checks

### Commit Message Guidelines

- Use present tense: "Add test" not "Added test"
- Be descriptive but concise
- Reference issues: "Fix #123: Add validation tests"

## Adding New Test Categories

If you're adding tests for a new feature area:

1. Create a new directory under `tests/`:
   ```bash
   mkdir tests/update
   ```

2. Add `__init__.py`:
   ```python
   """Update operation tests."""
   ```

3. Create test files following naming conventions

4. Add appropriate markers to `pytest.ini`:
   ```ini
   markers =
       update: Update operation tests
   ```

5. Update documentation in README.md

## Questions?

- Open an issue for questions about contributing
- Check existing tests for examples
- Review the RFC document for framework design

## Code of Conduct

This project follows the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
