# Result Analyzer

The Result Analyzer automatically processes pytest JSON reports and categorizes results by registered test markers.

## Features

- **Dynamic Marker Loading**: Reads markers directly from `pytest.ini` configuration
- **Single Source of Truth**: Markers defined only in `pytest.ini`
- **Configurable**: Can analyze reports from different projects with different marker configurations
- **CLI Tool**: `docdb-analyze` command for quick analysis
- **Class-Based API**: Testable, multi-context support

## Marker Detection

The analyzer uses a **whitelist approach** by reading registered markers from `pytest.ini`:

1. Parses the `[pytest]` markers section in `pytest.ini`
2. Extracts all registered marker names
3. Only includes markers that are explicitly registered
4. Automatically ignores pytest internals, test names, file paths, etc.

### Registered Markers
All markers used for categorization must be registered in `pytest.ini`:

```ini
[pytest]
markers =
    find: Find operation tests
    insert: Insert operation tests
    aggregate: Aggregation pipeline tests
    smoke: Quick smoke tests
    slow: Tests that take longer to execute
```

### Result
Only registered markers are used for categorization:
- Horizontal tags: `find`, `insert`, `update`, `delete`, `aggregate`, `index`, `admin`, `collection_mgmt`
- Vertical tags: `rbac`, `decimal128`, `collation`, `transactions`, `geospatial`, `text_search`, `validation`, `ttl`
- Special tags: `smoke`, `slow`

## Adding New Markers

1. Add the marker to `pytest.ini`:
   ```ini
   markers =
       mynewfeature: Description of my feature
   ```

2. Use it in your tests:
   ```python
   @pytest.mark.mynewfeature
   def test_something():
       pass
   ```

The analyzer will automatically include it in reports - no code changes needed!

## Failure Categorization

Tests are categorized into four types:

1. **PASS**: Test succeeded
2. **FAIL**: Test failed, feature exists but behaves incorrectly
3. **UNSUPPORTED**: Feature not implemented (skipped tests)
4. **INFRA_ERROR**: Infrastructure issue (connection, timeout, etc.)

## Usage

### CLI
```bash
# Quick analysis
docdb-analyze

# Custom input/output
docdb-analyze --input results.json --output report.txt
```

### Programmatic
```python
from result_analyzer import ResultAnalyzer, generate_report

# Create analyzer and run analysis
analyzer = ResultAnalyzer()
analysis = analyzer.analyze_results("report.json")

# Generate report
generate_report(analysis, "report.txt", format="text")
```

## Maintenance

The heuristic-based approach means:
- ✅ **No maintenance** for new test markers
- ✅ **Automatic adaptation** to new patterns
- ⚠️ **May need updates** if new fixture patterns emerge (e.g., new engine names)

To add a new fixture marker or engine name to exclude, update the filter in `analyzer.py`:

```python
# Skip fixture markers
if marker in {"documents", "mynewfixture"}:
    continue
    
# Skip engine names
if marker in {"documentdb", "mongodb", "mynewengine"}:
    continue
