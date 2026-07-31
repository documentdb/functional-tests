# Result Analyzer

Processes a pytest JSON report and generates a compatibility report, grouped by
feature, for a target engine.

## What it produces

From a pytest-json-report file it builds:

- A **verdict** (PASS / FAIL) with a one-line reason.
- A **breakdown** reconciling the run: collected = unsupported (deselected) +
  executed, and executed = passed + failed + errored + skipped + known gaps.
- **Needs attention**: failures and errors grouped by failure type, each with
  its traceback (capped for mass failures).
- **Known gaps**: xfailed tests (documented incompatibilities) with their reasons.
- **Skipped**: skipped tests with their reasons.
- **Feature breakdown**: a collapsible tree of pass/fail counts per feature,
  derived from each test's path (`core/operator/expressions/...`), down to the
  test file.

## Feature grouping

Grouping comes from the test's node id path, not from markers: the directory
tree under `tests/` *is* the feature taxonomy. Each path component is a tier
(area → category → family → operator → file), so no marker registration or
configuration is needed.

## Failure categorization

Failures/errors are tagged by the framework's assertion prefix (e.g.
`RESULT_MISMATCH`, `ERROR_MISMATCH`), or `INFRA_ERROR` when the exception type is
a known infrastructure type, or `UNKNOWN` when neither applies.

## Not applicable (unsupported) tests

Tests deselected at collection because the target lacks a required capability
(via `requires(...)`) are counted as "unsupported". A sidecar written next to
the report at collection time (`<report>.deselected.json`) records which
capability each needed, so the feature tree can explain why an area didn't run.

## Usage

### CLI

```bash
# Analyze the default report and print a summary
docdb-analyze

# Write a markdown report (for a GitHub step summary)
docdb-analyze --input results.json --output report.md --format markdown

# Other formats
docdb-analyze --output report.txt --format text
docdb-analyze --output analysis.json --format json
```

### Programmatic

```python
from result_analyzer import ResultAnalyzer, generate_report, print_summary

analyzer = ResultAnalyzer()
analysis = analyzer.analyze_results("report.json")

print_summary(analysis)
generate_report(analysis, "report.md", format="markdown")
```
