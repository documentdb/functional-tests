"""
Core behavioral tests for $mul update field operator.

Tests empty operand, multiple fields, dot notation, array index access,
and missing field creates zero.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EMPTY_OPERAND_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "empty_operand",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$mul": {}},
        expected={"_id": 1, "val": 10},
        msg="$mul with empty operand should be no-op",
    ),
]

ZERO_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "zero_field_multiplied",
        setup_docs=[{"_id": 1, "val": 0}],
        query={"_id": 1},
        update={"$mul": {"val": 99}},
        expected={"_id": 1, "val": 0},
        msg="$mul on field that is already 0 should remain 0",
    ),
]

MULTIPLE_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "multiple_fields",
        setup_docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        query={"_id": 1},
        update={"$mul": {"a": 2, "b": 3, "c": 4}},
        expected={"_id": 1, "a": 20, "b": 60, "c": 120},
        msg="$mul on multiple fields should multiply each independently",
    ),
    UpdateTestCase(
        "multiple_some_missing",
        setup_docs=[{"_id": 1, "a": 10}],
        query={"_id": 1},
        update={"$mul": {"a": 2, "b": 3}},
        expected={"_id": 1, "a": 20, "b": 0},
        msg="$mul on mix of existing/missing fields should multiply existing and create zero",
    ),
]

DOT_NOTATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "deeply_nested",
        setup_docs=[{"_id": 1, "a": {"b": {"c": {"d": 3}}}}],
        query={"_id": 1},
        update={"$mul": {"a.b.c.d": 2}},
        expected={"_id": 1, "a": {"b": {"c": {"d": 6}}}},
        msg="$mul on deeply nested field should work",
    ),
    UpdateTestCase(
        "creates_intermediate_docs",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$mul": {"a.b.c": 2}},
        expected={"_id": 1, "a": {"b": {"c": 0}}},
        msg="$mul on missing path should create intermediate documents",
    ),
    UpdateTestCase(
        "array_index",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$mul": {"arr.0": 2}},
        expected={"_id": 1, "arr": [20, 20, 30]},
        msg="$mul on array element by index should work",
    ),
    UpdateTestCase(
        "array_index_non_first",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$mul": {"arr.2": 3}},
        expected={"_id": 1, "arr": [10, 20, 90]},
        msg="$mul on non-first array element by index should work",
    ),
    UpdateTestCase(
        "array_index_out_of_bounds",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$mul": {"arr.5": 2}},
        expected={"_id": 1, "arr": [10, 20, 30, None, None, 0]},
        msg="$mul on out-of-bounds array index should pad with nulls and create zero",
    ),
    UpdateTestCase(
        "missing_nested_creates_zero",
        setup_docs=[{"_id": 1, "a": {"b": {}}}],
        query={"_id": 1},
        update={"$mul": {"a.b.c": 2}},
        expected={"_id": 1, "a": {"b": {"c": 0}}},
        msg="$mul on missing nested field should create zero",
    ),
]

MISSING_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "missing_int32_multiplier",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$mul": {"val": 2}},
        expected={"_id": 1, "val": 0},
        msg="$mul on missing field with int32 multiplier should create int32(0)",
    ),
    UpdateTestCase(
        "missing_int64_multiplier",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(5)}},
        expected={"_id": 1, "val": Int64(0)},
        msg="$mul on missing field with int64 multiplier should create int64(0)",
    ),
    UpdateTestCase(
        "missing_double_multiplier",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$mul": {"val": 2.5}},
        expected={"_id": 1, "val": 0.0},
        msg="$mul on missing field with double multiplier should create double(0.0)",
    ),
    UpdateTestCase(
        "missing_decimal128_multiplier",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("3")}},
        expected={"_id": 1, "val": Decimal128("0")},
        msg="$mul on missing field with decimal128 multiplier should create Decimal128(0)",
    ),
    UpdateTestCase(
        "missing_preserves_existing",
        setup_docs=[{"_id": 1, "other": "keep"}],
        query={"_id": 1},
        update={"$mul": {"val": 2}},
        expected={"_id": 1, "other": "keep", "val": 0},
        msg="$mul on missing field should preserve existing fields",
    ),
]

ALL_TESTS = (
    EMPTY_OPERAND_TESTS
    + ZERO_FIELD_TESTS
    + MULTIPLE_FIELD_TESTS
    + DOT_NOTATION_TESTS
    + MISSING_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_mul_core(collection, test: UpdateTestCase):
    """Test $mul core behavior."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
