# Test Format Guide

## Test Structure

Every API test follows: Setup → Execute → Assert.

```python
def test_descriptive_name(collection):
    """Clear description of what this test validates."""
    # Setup (insert documents if needed)
    collection.insert_many([{"_id": 0, "a": 1}, {"_id": 1, "a": 2}])
    
    # Execute — always use runCommand format
    result = execute_command(collection, {
        "find": collection.name,
        "filter": {"a": 1}
    })
    
    # Assert — use framework assertion helpers
    assertSuccess(result, [{"_id": 0, "a": 1}])
```

## Naming

**Files:** `test_<feature_area>.py` — files in feature subfolders must include the feature name.
```
✅ /tests/aggregate/unwind/test_unwind_path.py
❌ /tests/aggregate/unwind/test_path.py
```

**Functions:** `test_<what_is_being_tested>` — descriptive, self-documenting.
```
✅ test_find_with_gt_operator, test_unwind_preserves_null_arrays
❌ test_1, test_query, test_edge_case
```

## Assertions

Use helpers from `framework.assertions`, not plain `assert`:

```python
# assertResult — parametrized tests mixing success and error cases
assertResult(result, expected=5)          # checks cursor.firstBatch == [{"result": 5}]
assertResult(result, error_code=16555)    # checks error code only

# assertSuccess — raw command output
assertSuccess(result, [{"_id": 0, "a": 1}])
assertSuccess(result, expected, ignore_order=True)

# assertFailureCode — error cases (only check code, not message)
assertFailureCode(result, 14)
```

**One assertion per test function.** Split multiple assertions into separate tests.

## Fixtures

- `collection` — most common. Auto cleanup after test. Insert documents in test body.
- `database_client` — when you need multiple collections or database-level ops. Auto dropped after test.
- `engine_client` — raw client access.

## Execute Command

Always use `execute_command()` with runCommand format to get test result, not driver methods. Setups can use methods.

```python
# ✅ runCommand format
result = execute_command(collection, {"find": collection.name, "filter": {"a": 1}})

# ❌ Driver methods
result = collection.find({"a": 1})
```

## Helper Functions

Avoid deep helper function chains. One layer of abstraction on top of `execute_command()` is acceptable, don't add more abstraction layers unless justified.

```python
# ✅ Good: execute_expression wraps execute_command with aggregate pipeline boilerplate
result = execute_expression(collection, {"$add": [1, 2]})

# ❌ Bad: trivial wrappers that just save a few characters add indirection for no clarity gain
# result = execute_operator(collection, "$add", [1, 2])
```

Keep helpers in `utils/` at each test level. Helpers should reduce meaningful boilerplate (e.g., building an aggregate pipeline), not just shorten a single line.

Minimize helper scope — one helper should do one thing. If a helper has many if/else branches handling different cases, split it into separate helpers at a lower folder level.

## Parametrized Tests

Use `@pytest.mark.parametrize` with dataclasses for operators with many test cases:

```python
@dataclass(frozen=True)
class DivideTest(BaseTestCase):
    dividend: Any = None
    divisor: Any = None

DIVIDE_TESTS: list[DivideTest] = [
    DivideTest("int32", dividend=10, divisor=2, expected=5.0, msg="Should divide int32 values"),
    DivideTest("null_divisor", dividend=10, divisor=None, expected=None, msg="Should return null when divisor is null"),
    DivideTest("string_err", dividend=10, divisor="string", error_code=TYPE_MISMATCH_ERROR, msg="Should reject string"),
]

@pytest.mark.parametrize("test", DIVIDE_TESTS, ids=lambda t: t.id)
def test_divide(collection, test):
    """Test $divide operator."""
    result = execute_expression(collection, {"$divide": [test.dividend, test.divisor]})
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
```

- `BaseTestCase` (from `framework.test_case`) provides `id`, `expected`, `error_code`, `msg` — extend it per operator
- Shared helpers/dataclasses live in `utils/` at each level
- `msg` is **required** — describes expected behavior, not input
- Use constants from `framework.test_constants` (`INT32_MAX`, `FLOAT_NAN`, etc.) and `framework.error_codes` (`TYPE_MISMATCH_ERROR`, etc.)

## Validation

A pytest hook auto-validates during collection:
- Files must match `test_*.py` (except `__init__.py`)
- Test functions must have docstrings
- Must use assertion helpers, not plain `assert`
- One assertion per test function
- Must use `execute_command()` or helpers from utils
