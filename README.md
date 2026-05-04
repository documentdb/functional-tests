# DocumentDB Functional Tests

End-to-end functional testing framework for DocumentDB using pytest. This framework validates DocumentDB functionality against specifications through comprehensive test suites.

## Overview

This testing framework provides:

- **Specification-based Testing**: Tests define explicit expected behavior for DocumentDB features
- **Multi-Engine Support**: Run the same tests against DocumentDB, MongoDB, and other compatible engines
- **Parallel Execution**: Fast test execution using pytest-xdist
- **Tag-Based Organization**: Flexible test filtering using pytest markers
- **Result Analysis**: Automatic categorization and reporting of test results

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Access to a DocumentDB or MongoDB instance
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/documentdb/functional-tests.git
cd functional-tests

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

#### Basic Usage

```bash
# Run all tests against default localhost
pytest

# Run against specific engine
pytest --connection-string mongodb://localhost:27017 --engine-name documentdb

# Run with just connection string (engine-name defaults to "default")
pytest --connection-string mongodb://localhost:27017
```

#### Filter by Tags

```bash
# Run only find operation tests
pytest -m find

# Run smoke tests
pytest -m smoke

# Run find tests with RBAC
pytest -m "find and rbac"

# Exclude slow tests
pytest -m "not slow"
```

#### Parallel Execution

The framework supports parallel test execution using pytest-xdist, which can significantly reduce test execution time.

```bash
# Run with 4 parallel processes
pytest -n 4

# Auto-detect number of CPUs (recommended)
pytest -n auto

# Combine with other options
pytest -n auto -m smoke --connection-string mongodb://localhost:27017 --engine-name documentdb
```

**Two-Phase Execution:**
Some tests (e.g., `killAllSessions`, `setParameter`, `fsync`) modify global server state and cannot safely run in parallel. These are marked with `no_parallel`. When you use `-n`, the framework automatically:
1. **Phase 1**: Runs all parallel-safe tests with multiple workers
2. **Phase 2**: Runs `no_parallel` tests sequentially after Phase 1 completes

This is handled transparently — no extra flags needed.

**Performance Benefits:**
- Significantly faster test execution with multiple workers
- Scales with number of available CPU cores
- Particularly effective for large test suites

**Best Practices:**
- Use `-n auto` to automatically detect optimal worker count
- Parallel execution works best with 4+ workers
- Each worker runs tests in isolation (separate database/collection)
- Mark tests with `@pytest.mark.no_parallel` if they modify global server state (kill sessions/ops, change server parameters, drop all users/roles, etc.)

**When to Use:**
- Large test suites
- Local development for quick validation

**Example with full options:**
```bash
pytest -n 4 \
  --connection-string mongodb://localhost:27017 \
  --engine-name documentdb \
  -m "find or aggregate" \
  -v \
  --json-report --json-report-file=.test-results/report.json
```

#### Output Formats

```bash
# Generate JSON report
pytest --json-report --json-report-file=results.json

# Generate JUnit XML
pytest --junitxml=results.xml

# Verbose output
pytest -v

# Show local variables on failure
pytest -l
```

## Docker Usage

### Option 1: Use Pre-built Image (Recommended)

Pull the latest image from GitHub Container Registry:

```bash
# Pull latest version
docker pull ghcr.io/documentdb/functional-tests:latest

# Or pull a specific version
docker pull ghcr.io/documentdb/functional-tests:v1.0.0
```

Run tests with the pre-built image:

```bash
# Run all tests
docker run --network host \
  ghcr.io/documentdb/functional-tests:latest \
  --connection-string "mongodb://user:pass@host:port/?tls=true&tlsAllowInvalidCertificates=true" \
  --engine-name documentdb

# Run specific tags
docker run --network host \
  ghcr.io/documentdb/functional-tests:latest \
  -m smoke \
  --connection-string "mongodb://localhost:10260/?tls=true"

# Run with parallel execution
docker run --network host \
  ghcr.io/documentdb/functional-tests:latest \
  -n 4 \
  --connection-string mongodb://localhost:27017 \
  --engine-name documentdb
```

### Option 2: Build Locally

If you need to build from source:

```bash
docker build -t documentdb/functional-tests .
```

### Run Tests in Container

```bash
# Run against DocumentDB
docker run --network host \
  documentdb/functional-tests \
  --connection-string mongodb://localhost:27017 \
  --engine-name documentdb

# Run specific tags
docker run documentdb/functional-tests \
  --connection-string mongodb://cluster.docdb.amazonaws.com:27017 \
  --engine-name documentdb \
  -m smoke

# Run with parallel execution
docker run documentdb/functional-tests \
  --connection-string mongodb://localhost:27017 \
  --engine-name documentdb \
  -n 4
```

## Test Organization

Tests are organized by API operations with cross-cutting feature tags:

```
tests/
├── find/                    # Find operation tests
│   ├── test_basic_queries.py
│   ├── test_query_operators.py
│   └── test_projections.py
├── aggregate/               # Aggregation tests
│   ├── test_match_stage.py
│   └── test_group_stage.py
├── insert/                  # Insert operation tests
│   └── test_insert_operations.py
└── common/                  # Shared utilities
    └── assertions.py
```

## Test Tags

### Horizontal Tags (API Operations)
- `find`: Find operation tests
- `insert`: Insert operation tests
- `update`: Update operation tests
- `delete`: Delete operation tests
- `aggregate`: Aggregation pipeline tests
- `index`: Index management tests
- `admin`: Administrative command tests
- `collection_mgmt`: Collection management tests

### Vertical Tags (Cross-cutting Features)
- `rbac`: Role-based access control tests
- `decimal128`: Decimal128 data type tests
- `collation`: Collation and sorting tests
- `transactions`: Transaction tests
- `geospatial`: Geospatial query tests
- `text_search`: Text search tests
- `validation`: Schema validation tests
- `ttl`: Time-to-live index tests

### Special Tags
- `smoke`: Quick smoke tests for feature detection
- `slow`: Tests that take longer to execute
- `no_parallel`: Tests that must run sequentially (e.g., tests that kill sessions/ops, modify server config, or drop all users/roles). Automatically deferred to Phase 2 when using `-n`.
- `replica_set`: Tests that require a replica set topology (e.g., change streams, encryption, certain admin commands). Skipped by default in CI. To run locally, pass a replica set connection string: `pytest -m replica_set --connection-string "mongodb://localhost:27017/?directConnection=true"`

## Writing Tests

### Basic Test Structure

```python
import pytest
from tests.common.assertions import assert_document_match

@pytest.mark.find  # Required: operation tag
@pytest.mark.smoke  # Optional: additional tags
def test_find_with_filter(collection):
    """Test description."""
    # Arrange - Insert test data
    collection.insert_many([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ])
    
    # Act - Execute operation
    result = list(collection.find({"age": {"$gt": 25}}))
    
    # Assert - Verify results
    assert len(result) == 1
    assert_document_match(result[0], {"name": "Alice", "age": 30})
```

### Test Fixtures

- `engine_client`: MongoDB client for the engine
- `database_client`: Database with automatic cleanup
- `collection`: Collection with automatic test data setup and cleanup

### Custom Assertions

```python
from tests.common.assertions import (
    assert_document_match,
    assert_documents_match,
    assert_field_exists,
    assert_field_not_exists,
    assert_count
)

# Compare documents ignoring _id
assert_document_match(actual, expected, ignore_id=True)

# Compare lists of documents
assert_documents_match(actual_list, expected_list, ignore_doc_order=True)

# Check field existence
assert_field_exists(document, "user.name")
assert_field_not_exists(document, "password")

# Count documents matching filter
assert_count(collection, {"status": "active"}, 5)
```

## Result Analysis

The framework includes a command-line tool to analyze test results and generate detailed reports categorized by feature tags.

### Installation

```bash
# Install the package to get the CLI tool
pip install -e .
```

### CLI Tool Usage

```bash
# Analyze default report location
docdb-analyze

# Analyze specific report
docdb-analyze --input custom-results.json

# Generate text report
docdb-analyze --output report.txt --format text

# Generate JSON analysis
docdb-analyze --output analysis.json --format json

# Quiet mode (only write to file, no console output)
docdb-analyze --output report.txt --quiet

# Get help
docdb-analyze --help
```

### Programmatic Usage

You can also use the result analyzer as a Python library:

```python
from result_analyzer import ResultAnalyzer, generate_report, print_summary

# Create analyzer and analyze JSON report
analyzer = ResultAnalyzer()
analysis = analyzer.analyze_results(".test-results/report.json")

# Print summary to console
print_summary(analysis)

# Generate text report
generate_report(analysis, "report.txt", format="text")

# Generate JSON report
generate_report(analysis, "report.json", format="json")
```

### Failure Categories

Tests are automatically categorized into:
- **PASS**: Test succeeded, behavior matches specification
- **FAIL**: Test failed, feature exists but behaves incorrectly
- **UNSUPPORTED**: Feature not implemented
- **INFRA_ERROR**: Infrastructure issue (connection, timeout, etc.)

### Example Workflow

```bash
# Run tests with JSON report
pytest --connection-string mongodb://localhost:27017 \
       --engine-name documentdb \
       --json-report --json-report-file=.test-results/report.json

# Analyze results
docdb-analyze

# Generate detailed text report
docdb-analyze --output detailed-report.txt --format text

# Generate JSON for further processing
docdb-analyze --output analysis.json --format json
```

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8

# Type checking
mypy .
```

### Run Tests with Coverage

```bash
pytest --cov=. --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests following the test structure guidelines
4. Ensure tests pass locally
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/documentdb/functional-tests/issues
- Documentation: https://github.com/documentdb/functional-tests/docs
