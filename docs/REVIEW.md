# Code Review Guide

You are reviewing a pull request in this repository. Apply every rule below. For project context (framework, conventions, dev setup), read [`AGENTS.md`](../AGENTS.md) and [`CONTRIBUTING.md`](../CONTRIBUTING.md) first.

## Severity Levels

- 🔴 **Critical**: Missing error validation, tests that always pass, cleanup leaks, missing required coverage from [`TEST_COVERAGE.md`](testing/TEST_COVERAGE.md)
- 🟠 **Major**: Missing BSON type coverage, plain `assert`, driver methods instead of `execute_command`, overly complex new helpers, duplicate coverage with another folder, tests scoped to other features' contracts (out-of-scope)
- 🟡 **Minor**: Naming, documentation, file organization, redundant cases within the same folder, missing `# Property [...]:` comments
- 🟢 **Nitpick**: Style preferences, minor improvements

## How to Review

1. Read [`docs/testing/TEST_FORMAT.md`](testing/TEST_FORMAT.md), [`docs/testing/TEST_COVERAGE.md`](testing/TEST_COVERAGE.md), [`docs/testing/FOLDER_STRUCTURE.md`](testing/FOLDER_STRUCTURE.md) — they're the source of truth.
2. For each rule in those docs, check whether it applies to the PR's feature.
3. If a rule applies, verify the PR has **exact coverage** specified by that rule — no gaps, no extras that don't match the spec.
4. Walk every section of the checklist below.

## Review Checklist

### 1. Test Format Compliance

Follow every rule in [`TEST_FORMAT.md`](testing/TEST_FORMAT.md). Additionally enforce:

- **Strict BSON numeric types**: Expected values and check arguments must use the exact BSON type the server returns (`Int64` vs `int` vs `float`, `Decimal128`).

### 2. Test Coverage

Follow every rule in [`TEST_COVERAGE.md`](testing/TEST_COVERAGE.md). For each rule that applies to the PR's feature, verify exact coverage — every specified case must be present.

### 3. Folder Structure

Follow every rule in [`FOLDER_STRUCTURE.md`](testing/FOLDER_STRUCTURE.md). Additionally enforce:

- **Feature ownership**: Tests belong in the feature's own folder. `$abs` type validation goes in `expressions/arithmetic/abs/`, not in `stages/project/`. Testing `$abs` inside `$project` is a `$project` context test (one simple case), not an `$abs` test.

### 4. Parametrized Test Quality

- [ ] Uses `@dataclass(frozen=True)` extending `BaseTestCase`
- [ ] Uses `pytest_params()` from `framework.parametrize`
- [ ] Test IDs are unique and descriptive
- [ ] Constants from `framework.test_constants` used (not magic numbers)
- [ ] Error codes from `framework.error_codes` used (not raw integers)
- [ ] Properties/groups are commented with `# Property [Name]: description`

### 5. Framework Usage

- [ ] `execute_command()` for all test operations (setup can use driver methods)
- [ ] `assertResult()` for parametrized tests mixing success/error cases
- [ ] `assertSuccess()` for cursor-based results
- [ ] `assertFailureCode()` for error-only assertions
- [ ] `assertProperties()` for structural assertions (existence, type checks)
- [ ] No deep helper chains — one layer of abstraction max
- [ ] Helpers in `utils/` at the appropriate level

### 6. Code Quality

- [ ] No code duplication across test files
- [ ] Shared test data in `utils/` modules
- [ ] Type annotations on helper functions
- [ ] Order-independent output uses `ignore_doc_order=True`
- [ ] Tests that require a replica set are tagged `@pytest.mark.replica`
- [ ] Tests that cannot run in parallel are tagged `@pytest.mark.no_parallel`
- [ ] Tests where MongoDB itself fails are tagged with `engine_xfail` (not skipped)
- [ ] Tests with non-deterministic output (e.g. `$rand`, `$sample`, server timestamps) assert structure/bounds, not exact values

### 7. Test Isolation & Safety

- [ ] Tests use the `collection` fixture (auto-cleanup)
- [ ] Per-test-case fixtures handle cleanup (drop the database). Validate other resources are cleaned up too — e.g. users created during the test
- [ ] No hardcoded collection/database names (use fixture-derived names)
- [ ] Tests are parallelizable (no shared state)
- [ ] `TargetCollection` subclasses used for special collection types

### 8. Correctness

- [ ] Numeric type assertions use strict BSON types (`int` vs `Int64` vs `float`)
- [ ] Date assertions use UTC-aware datetimes
- [ ] Order-dependent assertions don't use `ignore_doc_order` incorrectly
- [ ] Error cases test the right error code (not just "any error")
- [ ] **Undocumented type coercion** is tested per command when the engine's accepted-type set is broader than the spec documents (numeric→bool, whole-double→int, null-as-omitted, etc.). Engines may diverge there; documented-only coverage hides the gap. Applies to any param type — bool, int, string, document — not just bool. Skip when §19 Foundational Spec Behaviors covers it, or when the coercion is identical across consumers and centralized somewhere. When in doubt, mirror the matrix from the most thoroughly-tested consumer of the same parameter (e.g. for `bypassDocumentValidation`, see `tests/core/aggregation/commands/aggregate/test_aggregate_bypass_validation.py`).

### 9. Documentation Updates

- [ ] [`TEST_COVERAGE.md`](testing/TEST_COVERAGE.md) updated if the PR introduces coverage rules for a new feature category (e.g. date operators, window functions)
- [ ] [`TEST_FORMAT.md`](testing/TEST_FORMAT.md) updated if the PR introduces new patterns (e.g. new assertion helpers, new marks, new parametrize utilities)
- [ ] [`FOLDER_STRUCTURE.md`](testing/FOLDER_STRUCTURE.md) updated if the PR adds new top-level test directories or changes the feature taxonomy
- [ ] [`CONTRIBUTING.md`](../CONTRIBUTING.md) updated if the PR changes setup steps, workflows, or contribution process
- [ ] [`README.md`](../README.md) updated if the PR changes project usage, configuration, or public-facing instructions

## What Not to Flag

- **Don't claim an expected value may not match MongoDB behavior.** CI runs the same suite against MongoDB and validates expected values; that's the source of truth.
- **Don't recommend `engine_xfail("documentdb")`** for live DocumentDB failures — engine xfails aren't handled in this repo.
- **Don't suggest tests** for parse-time vs runtime behavior, optimizer paths, or other internal mechanics that aren't user-observable.
- **Don't suggest replacing `pytest.approx(nan_ok=True)`** — it's the established NaN idiom in this codebase.
- **Don't flag a `Binary` subtype 0** expressed as `Binary` in the inserted document and `bytes` in the expected value — PyMongo decodes subtype 0 to `bytes`, so this pairing is the only working pattern.
- **Don't flag long parametrized files** for line count alone when cases are logically grouped.
- **Don't ask for an exhaustive BSON-type matrix** on simple shared parameters like `comment` — representative cases are enough.
- **Don't flag undocumented coercion tests as "over-spec".** When a parameter's accepted-type set in practice is broader than the spec documents (e.g. `bypassDocumentValidation` accepts numerics despite being typed as boolean), per-command coercion tests are load-bearing — see Correctness checklist §8.
- **Don't flag stylistic preferences** that pre-commit (black, isort, flake8) already enforces.

## Tone

- Be constructive and respectful.
- Explain the reasoning behind suggestions.
- Distinguish required changes from optional suggestions with prefixes: `[Required]`, `[Suggestion]`, `[Question]`, `[Nitpick]`.
- Acknowledge good test design and thorough coverage.

## Output Format

Structure your review as:

```markdown
## Summary
Brief overview of the changes and overall assessment.

## Critical Issues
Blocking issues that must be fixed.

## Suggestions
Improvements that would enhance the tests.

## Questions
Clarifications needed to complete the review.

## Positive Feedback
Highlight well-designed tests or good coverage patterns.
```
