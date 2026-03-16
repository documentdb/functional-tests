# Folder Structure Guide

## Core Principles

1. **Feature-specific tests** → dedicated subfolders. Test only the feature's own inputs and edge cases, not lower-level features it contains (those are tested in their own directories).
2. **Cross-cutting features** (rbac, transactions, collation, etc.) → own top-level folders, NOT under feature-specific folders (e.g., rbac with find goes under `/tests/rbac/`, not `/tests/find/`).
3. **Feature levels** — higher-level features (e.g., `find`, `$group`, `$lookup`) contain lower-level features (e.g., `projection`, `$sum`, `$unwind`). Higher-level tests only verify lower-level features are supported (1-2 cases) and test combinations of lower-level features. Lower-level features test their own edge cases in their own directories.
4. **Integration tests** (multiple same-level features interacting) → parent folders. Example: `{$add: [{$subtract: [2, 1]}, 3]}` tests multiple operators working together (operator combination/nesting), not a single operator's edge cases — goes in `expressions/test_expression_combination.py`, not `expressions/arithmetic/add/`. Single operator edge cases (null handling, type errors, boundary values) stay in the operator's own folder.
5. **Operators** → comprehensive tests in `/tests/operators/{type}/$operator/`, only 1-2 integration cases elsewhere.

6. **File organization** — a feature folder can have multiple files if a single file would exceed ~200 lines. Group test cases logically by aspect (e.g., by parameter, by error type). Example:
```
/tests/aggregate/unwind/
├── test_unwind_path.py                           # path parameter
├── test_unwind_preserve_null_and_empty_arrays.py # preserveNullAndEmptyArrays option
└── test_unwind_combined_options.py               # multiple options together
```

## Decision Tree

**Step 1: Cross-cutting feature?** (rbac, transactions, collation, geospatial, text_search, validation, ttl)
→ YES: `/tests/{feature}/`

**Step 2: Operator?** ($in, $gt, $sum, $add, etc.)
→ YES comprehensive: `/tests/operators/{type}/$operator/`
→ YES integration: 1-2 cases in the higher-level feature that uses it (e.g., `$sum` in `$group/`, `$add` in `$project/`, `$gt` in `$match/`+`$expr/`)

**Step 3: Single parameter/option of a feature?**
→ YES: feature subfolder (e.g., `/tests/aggregate/unwind/`)

**Container features** ($expr, $match, $lookup): under the container's directory, only test that sub-features work inside it — one test case per sub-feature, no edge cases. Edge cases belong in each sub-feature's own directory.
- `$expr/` → one test per operator usable inside $expr
- `$lookup/` → 1-2 cases per pipeline sub-stage

**Step 4: Interaction between multiple same-level features?**
→ YES: parent folder (e.g., `{$add: [{$subtract: ...}]}` tests expression nesting, not `$add` itself — goes in `expressions/`, not `add/`)


**Step 5: Basic operation behavior?**
→ operation folder (e.g., `/tests/find/test_basic_queries.py`)

## Anti-patterns

- ❌ Cross-cutting tests in operation folders
- ❌ Comprehensive operator tests outside `/operators/`
- ❌ Integration tests in feature subfolders (they belong in parent)
- ❌ 200+ test functions in one file (split by feature)


## Feature Tree

The test directory structure maps to the DocumentDB feature taxonomy defined in [`docs/feature-tree.csv`](../feature-tree.csv).

Each row in the CSV represents a feature path:
```
Category,Subcategory1,Subcategory2,Subcategory3,Subcategory4,Item
```

Example mappings:
| Feature | CSV Path | Test Directory |
|---------|----------|----------------|
| `$group` stage | `core,operator,aggregation,pipeline,-,group` | `tests/core/operator/stages/group/` |
| `$sum` accumulator | `core,operator,aggregation,accumulators,-,sum` | `tests/core/operator/accumulators/sum/` |
| `$mul` update | `core,operator,update,fields,-,mul` | `tests/core/operator/update/fields/mul/` |
| `find` command | `core,crud,commands,-,-,find` | `tests/find/` |

Use the feature tree to:
- Determine where a new test file should go
- Find related tests by feature hierarchy
- Ensure complete coverage across feature areas
