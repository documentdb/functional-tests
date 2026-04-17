# DocumentDB Comprehensive Test Coverage Guidelines

**Purpose**: Define comprehensive test coverage requirements for DocumentDB features to ensure complete validation.

---

## Core Testing Principles

### 1. Data Type Coverage
**Rule**: Every command/operator input must be tested with ALL DocumentDB data types. Use constants and datasets from `framework/test_constants.py` for consistent test values.

**Standard Data Types** (non-deprecated BSON types):
- **Numeric**: double, int, long, decimal128 → `NUMERIC`, `NUMERIC_INT32`, `NUMERIC_INT64`, `NUMERIC_DOUBLE`, `NUMERIC_DECIMAL128`
- **String**: string
- **Boolean**: bool
- **Date**: date
- **Null**: null
- **Object**: object
- **Array**: array
- **Binary data**: binData
- **ObjectId**: objectId
- **Regular Expression**: regex
- **JavaScript**: javascript
- **Timestamp**: timestamp
- **MinKey**: minKey
- **MaxKey**: maxKey

**Type Test Matrix**:
- Valid types (should succeed)
- Invalid types (should fail with appropriate error code)
- Type conversion behavior
- Type precedence in operations

---

### 2. Arithmetic Operator Coverage
**Rule**: Arithmetic operators must test all numeric type combinations and edge cases.

**Multi-Input Operators** (e.g., $add, $subtract, $multiply, $divide, $mod):

**Numeric Type Combinations**:
```
double + double → double
double + int → double
double + long → double
double + decimal128 → decimal128
int + int → int
int + long → long
int + decimal128 → decimal128
long + long → long
long + decimal128 → decimal128
decimal128 + decimal128 → decimal128
```

**Single-Input Operators** (e.g., $ln, $log10, $exp, $abs, $ceil, $floor, $sqrt, $trunc):

**Input → Output Type Conversion**:
```
double → double
int → double (for operators that produce non-integer results like $ln, $exp, $sqrt)
int → int (for operators that preserve integers like $abs, $ceil, $floor, $trunc)
long → double (for operators that produce non-integer results)
long → long (for operators that preserve integers)
decimal128 → decimal128
```
Note: Check each operator's specific return type rules. The general pattern is: decimal128 input always returns decimal128; other numeric types return double unless the operator preserves integer types.

Note: Distinguish between fractional doubles (2.5) and whole-number doubles (3.0). Some operators coerce whole-number doubles to int, producing different behavior than fractional doubles.

**Edge Cases for Arithmetic**:
- **NaN handling**: operation with NaN → NaN
- **Infinity handling**: 
  - number + Infinity → Infinity
  - Infinity + Infinity → Infinity
  - Infinity + (-Infinity) → NaN
  - -Infinity + (-Infinity) → -Infinity
- **Overflow**: `INT32_MAX` + 1 → long, `INT64_MAX` + 1 → double
- **Underflow**: `INT32_MIN` - 1 → long, `INT64_MIN` - 1 → double
- **Sign handling**: positive, negative, zero
- **Negative zero**: `DOUBLE_NEGATIVE_ZERO` → verify behavior (some operators normalize to `0.0`, others preserve `-0.0`); `DECIMAL128_NEGATIVE_ZERO` → verify; `NumberDecimal("-0E+N")` and `NumberDecimal("-0E-N")` → verify exponent preservation
- **Special values**: MinKey, MaxKey combinations
- **Two's complement asymmetry (single-input operators)**: `INT32_MIN` has no positive int counterpart → must promote to long; `INT64_MIN` has no positive long counterpart → verify overflow/error behavior
- **Double precision boundaries**: `DOUBLE_NEAR_MAX`, `DOUBLE_MIN_SUBNORMAL`, `DOUBLE_MIN_NEGATIVE_SUBNORMAL`, `DOUBLE_NEAR_MIN`, `DOUBLE_NEGATIVE_ZERO` → use `NUMERIC_DOUBLE` from `test_constants.py`

---

### 3. Expression Type Coverage
**Rule**: Expression types and field paths must be tested at two levels: thorough expression engine tests (under `expressions/`) that cover shared behavior like field path resolution and nesting, and per-operator smoke tests (under each operator's folder) that confirm each operator accepts each expression type.

**Expression Types**:
- **Literal**: `1`, `"hello"`, `true`
- **Field**: `"$x"`, `"$a.b"`
- **System Variables**: `$$ROOT`, `$$CURRENT`, `$$REMOVE`
- **Expression operator**: `{$abs: -1}`, `{$add: [1, 2]}`
- **Array expression**: `["$x", "$y"]`, `[{$abs: -1}]`
- **Object expression**: `{a: "$x"}`, `{a: {$abs: -1}}`

#### Expression Engine Tests (under `expressions/`)
Tests the expression parser/evaluator mechanics (field path resolution, nesting, system variables). These are shared behavior across all operators — run once with a representative operator.

Example path: `documentdb_tests/compatibility/tests/core/operator/expressions/test_field_paths.py`

**Embedding/Nesting (thorough)**:
- Expression in object: `{a: {$abs: -1}}`
- Expression in array: `[{$abs: -1}]`
- Nested expressions: `{$add: [{$abs: "$x"}, {$abs: "$y"}]}`
- Deep nesting: `{$add: [1, {$abs: {$ceil: {$sqrt: "$x"}}}]}`
- Complex: `{a: [{$add: [1, {$abs: "$x"}]}, {b: {$ceil: "$y"}}]}`

**Field Path Resolution (thorough)**:
- Simple: `"$a"` on `{a: 1}`
- Nested object: `"$a.b"` on `{a: {b: 1}}`
- Composite array: `"$a.b"` on `{a: [{b: 1}, {b: 2}]}`
- Array index: `"$a.0.b"` on `{a: [{b: 1}, {b: 2}]}`
- Nested arrays: `"$a.b"` on `{a: [[{b: 1}], [{b: 2}]]}`
- Deep nested: `"$a.b.c.d"` on `{a: {b: [{c: [{d: 1}]}]}}`
- Non-existent: `"$missing"` → null
- Non-existent nested: `"$x.y.0"` on `{}`
- Array index path in expression context: `"$a.0.b"` — valid in filter query, verify behavior in aggregation expressions

**System Variables (thorough)**:
- `$$ROOT` in various nesting contexts
- `$$CURRENT` equivalence to field paths
- `$$REMOVE` in conditional branches
- `$let` with complex variable definitions

#### Per-Operator Tests (under each operator's folder)
Each operator must test these because behavior differs per operator and per input.

Example path: `documentdb_tests/compatibility/tests/core/operator/expressions/arithmetic/divide/test_divide.py`

**Per-operator expression type tests (one test per type)**: Each operator must verify it handles each expression type correctly, as behavior may differ per operator:
- With array expression input: `{$add: [["$x", "$y"]]}` — array containing field references
- With object expression input: `{$add: {a: "$x"}}` — object with field reference values
- With composite array input: doc `{a: [{b: 1}, {b: 2}]}`, expression `{$add: "$a.b"}` — field path resolving to array from array-of-objects

**`$missing` field behavior**: operators handling differ. Must test per operator and per input position

**Array index paths in expression context**: `"$a.0.b"` — verify whether the operator supports this for `{"a": {"0": {"b": 1}}}` or `{"a": [{"b": 1}, {"b": 2}]}`

**System variables**: only test if the official documentation says the operator supports them

---

### 4. Argument Handling
**Rule 1**: Test various argument counts and formats.

**Argument Count Variations**:
- **No arguments**: `{$add: []}`
- **Single argument**: `{$add: [1]}` and `{$add: 1}`
- **Two arguments**: `{$add: [1, 2]}`
- **Multiple arguments**: `{$add: [1, 2, 3, 4]}`

**Rule 2**: Each input position must be tested independently against all applicable rules. Different input positions may accept different types.

**Per-Input-Position Coverage**:
- **Data types**: test every valid and invalid data type per position
- **Expression types**: literal, field, expression operator, array expression, object expression per position
- **All other applicable rules** from this document (edge cases, special values, etc.)

**Examples**:
- `$add`: 2 kinds of input — 1st accepts date or numeric; 2nd and beyond accept numeric only.
- `$sum`: 1 kind of input — all inputs are numeric, test rules once on any single input position (no need to repeat for each position).
- `$subtract`: 2 inputs, each must be tested with every data type, expression type, and applicable rules independently.
- `$cond`: 3 inputs (condition, then, else) — each has different valid types and semantics.

**Rule 3**: Test correlations between inputs that interact. Only test meaningful combinations where both inputs are valid types but their interaction produces different behavior.

**Correlation Testing**:
- Identify which inputs interact (affect each other's behavior or output)
- Test valid cross-input combinations that produce different behavior
- Skip combinations where one input doesn't affect the other's semantics
- Skip (invalid, invalid) pairs — different engines may parse inputs in different order, returning different error codes for the same (invalid, invalid) combination. Per-input tests already verify each invalid type is rejected.

**Examples**:
- `$add`: 1st is date → test 2nd with all numeric types (int/long/double/decimal128). No need to test 2nd with invalid types again (already covered by per-input testing).
- `$unwind`: `path` and `includeArrayIndex` can conflict (same path) → test permutations. `preserveNullAndEmptyArrays` has no significant interaction with the other two → no correlation tests needed.

---

### 5. Date Arithmetic Coverage
**Rule**: Date operations must test numeric additions and special cases.

**Date Test Cases**:
- **Date + numeric types**: ISODate + int/long/double/decimal128
- **Rounding behavior**: Date + fractional values: `0.1`, `0.49`, `0.5`, `0.51`, `0.6`, `1.5`, `-0.5`, `-0.51`
- **Invalid combinations**:
  - Date + Date (should fail)
  - Date + Infinity (should fail)
  - Date + NaN (should fail)
  - Date + non-numeric types (should fail)
- **Overflow**: Date + LONG_MAX (should fail)
- **Timezone awareness**: Use `CodecOptions(tz_aware=True, tzinfo=timezone.utc)` to verify timezone-aware datetime decoding, e.g. `datetime(2024, 1, 1, tzinfo=timezone.utc)`

---

### 6. Error Code Validation
**Rule**: Invalid operations must return correct error codes. Only assert on error codes, not error messages — messages are not part of the spec and may change between versions.

**Error Test Pattern**:
```
For each invalid_type in [string, object, array, ...]:
    Test operation with invalid_type fails with error code X
```

---

### 7. Decimal128 Precision Coverage
**Rule**: Decimal128 operations must test precision boundaries. Use `NUMERIC_DECIMAL128` and individual constants from `test_constants.py` (e.g., `DECIMAL128_MAX`, `DECIMAL128_MIN`, `DECIMAL128_SMALL_EXPONENT`).

**Decimal128 Test Cases**:
- **Precision boundaries**: `DECIMAL128_MAX`, `DECIMAL128_MIN`, `DECIMAL128_SMALL_EXPONENT`, `DECIMAL128_LARGE_EXPONENT`, `DECIMAL128_ZERO`, `DECIMAL128_NEGATIVE_ZERO`
- **High precision**: Results with >35 digits
- **Exponent boundaries**: Maximum and minimum exponents
- **Rounding behavior**: Precision loss scenarios
- **Special values**: Decimal128 Infinity, NaN

---

### 8. Null Field Handling
**Rule**: Test null propagation and missing field behavior.

**Null Patterns**:
- **Null propagation**: operation(value, null) → null
- **Null + Null**: null

---

### 9. Numeric Equivalence in Grouping/Comparison
**Rule**: Test that numerically equivalent values across types are treated as identical for grouping, matching, and deduplication.

**Equivalence Groups**:
- `NumberInt(1)`, `NumberLong(1)`, `1.0`, `NumberDecimal("1")` → same group
- `NumberInt(0)`, `NumberLong(0)`, `0.0`, `NumberDecimal("0")` → same group
- `false` vs `0`, `true` vs `1` → **NOT** equivalent (BSON type distinction)

**Applies to**: `$group`, `$match`, `$lookup`, `$addToSet`, `$setUnion`, `$setIntersection`, indexes, `$eq`/`$ne` comparisons, `distinct`

---

### 10. BSON Type Distinction
**Rule**: Test that values of different BSON types are treated as distinct even when they appear equivalent in some languages.

**Key Distinctions**:
- `false` vs `NumberInt(0)` → distinct
- `true` vs `NumberInt(1)` → distinct
- `null` vs `$missing` → check per-operator (some treat as same, some don't)
- `""` (empty string) vs `null` → distinct

**Applies to**: any context involving comparison, grouping, deduplication, or matching

---

### 11. Expression Operator in Pipeline Contexts
**Rule**: Each expression operator must have one test case in each pipeline context. When generating tests for an operator (e.g., `$add`), create one test case per context in the corresponding stage/feature folder.

**Pipeline Contexts** (one test case per operator per context):
- In `core/operator/aggregation/stages/project`: `{$project: {result: {$op: "$field"}}}`
- In `core/operator/aggregation/stages/addFields`: `{$addFields: {result: {$op: "$field"}}}`
- In `core/operator/aggregation/stages/match` with `$expr`: `{$match: {$expr: {$gt: [{$op: "$field"}, value]}}}`
- In `core/operator/aggregation/stages/group` expression: `{$group: {_id: null, result: {$max: {$op: "$field"}}}}` and `{$group: {_id: {$max: {$op: "$field"}}}}`
- Don't need to add for every operator in find filter $expr: (should have same behavior with aggregation with $expr)
- Don't need to add for every operator in `find()` computed projection: (should have same behavior with aggregation)
- Don't need to add for every operator in `core/operator/aggregation/stages/set`: (alias for `$addFields`, separate code path)
- Don't need to add for every operator in `$lookup` and `$facet` pipeline: (too deep nesting)

**Example**: generating `$add` tests adds test cases in these files:
- `stages/project/test_operators_in_project.py`
- `stages/addFields/test_operators_in_addFields.py`
- `stages/match/test_operators_in_match_expr.py`
- `stages/group/test_operators_in_group.py`

**Applies to**: all expression operators (`$abs`, `$add`, `$ceil`, `$floor`, `$sqrt`, `$concat`, etc.)

---


### 12. Object Expression Test Coverage
**Rule**: All sizes, shapes, and types of documents must be tested in object expressions.

**Key Cases**:
- Documents of different shapes must be tested:
  - Empty documents
  - Flat documents, including all scalar types
  - Deeply nested documents ($a.b.c.d)
  - Nested arrays (`{arr: [[1,2], [3,4]]}`, `{obj: {arr: [1,2,3]}}`)
- For object manipulation:
  - Overwriting existing fields returns object with new value
  - Removing non-existent fields has no effect and returns original object
  - Original document is not updated, only the returned object
  - $set/unsetField does not traverse objects or arrays, it only works upon top level fields
    - Test this using $replaceWith
  - Field names with periods or dollar ($) signs require $replaceWith
- Inputs other than objects, nulls, or undefined values are rejected
- Verify that $mergeObjects accepts an array of any number of objects
- For $mergeObjects, verify that field conflicts prioritize the last document

**Applies to**: object expression operators (`$mergeObjects`, `$setField`, `$unsetField`, `$getField`)

---

## Test Category Checklist

For any DocumentDB feature, ensure coverage of:

- [ ] **Argument handling**: empty, single, multiple arguments; per-input-position coverage of types, expressions, and applicable rules
- [ ] **Input correlation**: meaningful cross-input combinations where inputs interact; skip redundant invalid-type cross-products
- [ ] **Expression types (per-operator)**: one test per type — literal, field, expression operator, array expression input (`[["$x", "$y"]]`), object expression input (`{a: "$x"}`)
- [ ] **`$missing` field behavior**: per operator, per input position
- [ ] **Array index paths**: `$a.0.b` in expression context — verify validity outside filter queries
- [ ] **Null/$missing propagation**: per operator, per input position — short-circuit vs propagate vs ignore
- [ ] **NaN handling**: NaN propagation and combinations
- [ ] **Infinity handling**: Infinity, -Infinity combinations
- [ ] **Type validation**: all valid and invalid types
- [ ] **Date arithmetic**: date operations and edge cases (if applicable)
- [ ] **Edge cases**: boundary values, special combinations
- [ ] **Field lookup**: simple, nested, array, non-existent, composite, composite array
- [ ] **Sign handling**: positive, negative, zero
- [ ] **Type conversion**: all numeric type combinations
- [ ] **Overflow handling**: `INT32_MAX`, `INT64_MAX` boundaries
- [ ] **Underflow handling**: `INT32_MIN`, `INT64_MIN` boundaries
- [ ] **Decimal128 precision**: high precision, boundaries (if applicable)
- [ ] **Error codes**: correct error codes for invalid operations
- [ ] **Numeric equivalence**: equivalent values across numeric types grouped/matched correctly (if applicable)
- [ ] **BSON type distinction**: different BSON types treated as distinct (if applicable)
- [ ] **Pipeline stage interaction**: interaction with preceding/following stages (if pipeline stage)
- [ ] **Pipeline contexts**: one test case per operator per context — $project, $addFields, $match+$expr, $group (if expression operator)
- [ ] **System variables**: $$ROOT, $$CURRENT, $$REMOVE, $let — only if official documentation says supported
- [ ] **Negative zero**: `DOUBLE_NEGATIVE_ZERO` and `DECIMAL128_NEGATIVE_ZERO` behavior (if numeric operator)
- [ ] **Double precision boundaries**: `DOUBLE_NEAR_MAX`, `DOUBLE_MIN_SUBNORMAL`, `DOUBLE_NEAR_MIN` (if accepts double)

---

## Standard Test Datasets

All test constants and datasets are defined in `framework/test_constants.py`. Import from there — do not duplicate values.

**Key datasets**:
- `NUMERIC` — all numeric boundary values across int32, int64, double, float, decimal128
- `NUMERIC_INT32`, `NUMERIC_INT64`, `NUMERIC_DOUBLE`, `NUMERIC_FLOAT`, `NUMERIC_DECIMAL128` — per-type lists
- `NEGATIVE_NUMERIC`, `ZERO_NUMERIC`, `POSITIVE_NUMERIC` — sign-grouped lists
- `NOT_A_NUMBER` — `float("nan")`, `Decimal128("nan")`
- Individual constants: `INT32_MIN`, `INT32_MAX`, `INT64_MIN`, `INT64_MAX`, `DOUBLE_NEGATIVE_ZERO`, `DECIMAL128_MAX`, `DECIMAL128_MIN`, `MISSING`, etc.

**Not yet in `test_constants.py`** (add as needed):
- Date dataset (ISODate values)
- Non-numeric dataset (string, object, array, BinData, ObjectId, bool, Timestamp, MinKey, MaxKey, UUID)

---
