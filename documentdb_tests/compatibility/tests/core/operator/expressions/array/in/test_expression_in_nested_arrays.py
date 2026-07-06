"""
Nested array search tests for $in expression.

Tests searching for complex elements in nested mixed arrays and deeply nested structures.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, MaxKey, MinKey, ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Success: nested mixed arrays as search targets
# ---------------------------------------------------------------------------
NESTED_MIXED_ARRAY_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="nested_find_object_in_mixed",
        value={"a": 1},
        array=[1, "two", {"a": 1}, [3, 4], True],
        expected=True,
        msg="Should find object in nested mixed array",
    ),
    ArrayTestClass(
        id="nested_find_array_in_mixed",
        value=[3, 4],
        array=[1, "two", {"a": 1}, [3, 4], True],
        expected=True,
        msg="Should find array in nested mixed array",
    ),
    ArrayTestClass(
        id="nested_find_deep_object",
        value={"a": {"b": 3}},
        array=[[1, 2], {"a": {"b": 3}}, "x"],
        expected=True,
        msg="Should find deep object in array",
    ),
    ArrayTestClass(
        id="nested_find_array_with_mixed_types",
        value=[None, "a", 2],
        array=[1, [None, "a", 2], "b"],
        expected=True,
        msg="Should find mixed-type subarray",
    ),
    ArrayTestClass(
        id="nested_find_empty_object",
        value={},
        array=[1, {}, [2], "a"],
        expected=True,
        msg="Should find empty object in array",
    ),
    ArrayTestClass(
        id="nested_find_empty_array",
        value=[],
        array=[1, {}, [], "a"],
        expected=True,
        msg="Should find empty array in array",
    ),
    ArrayTestClass(
        id="nested_find_subarray_binary_decimal128",
        value=[Binary(b"\x01\x02", 0), Decimal128("3.14")],
        array=[1, [Binary(b"\x01\x02", 0), Decimal128("3.14")], "x", [3]],
        expected=True,
        msg="Should find subarray with binary and decimal128",
    ),
    ArrayTestClass(
        id="nested_find_subarray_object_array",
        value=[{"k": 1}, [2, 3]],
        array=["a", [{"k": 1}, [2, 3]], None, 4],
        expected=True,
        msg="Should find subarray with object and array",
    ),
    ArrayTestClass(
        id="nested_find_subarray_datetime_objectid",
        value=[datetime(2024, 1, 1), ObjectId("000000000000000000000001")],
        array=[0, [datetime(2024, 1, 1), ObjectId("000000000000000000000001")], "end"],
        expected=True,
        msg="Should find subarray with datetime and objectid",
    ),
    ArrayTestClass(
        id="nested_find_subarray_minkey_maxkey",
        value=[MinKey(), MaxKey()],
        array=[[MinKey(), MaxKey()], 1, "a"],
        expected=True,
        msg="Should find subarray with minkey and maxkey",
    ),
]

# ---------------------------------------------------------------------------
# Success: deeply nested search targets (3-5 levels)
# ---------------------------------------------------------------------------
DEEPLY_NESTED_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="nested_3_levels",
        value=[[2, 3], [4, 5]],
        array=[1, [[2, 3], [4, 5]], "end"],
        expected=True,
        msg="Should find 3-level nested array",
    ),
    ArrayTestClass(
        id="nested_4_levels",
        value=[[[1, 2], 3], 4],
        array=["a", [[[1, 2], 3], 4], None],
        expected=True,
        msg="Should find 4-level nested array",
    ),
    ArrayTestClass(
        id="nested_deep_mixed_bson",
        value=[[MinKey(), {"a": [Decimal128("1.5")]}], True],
        array=[0, [[MinKey(), {"a": [Decimal128("1.5")]}], True], "x"],
        expected=True,
        msg="Should find deeply nested mixed BSON",
    ),
    ArrayTestClass(
        id="nested_inner_not_outer",
        value=[2, 3],
        array=[[1, [2, 3]], [2, 3], 4],
        expected=True,
        msg="Should find inner array match",
    ),
    ArrayTestClass(
        id="nested_5_levels",
        value=[[[[99]]]],
        array=[[[[[99]]]], "other"],
        expected=True,
        msg="Should find 5-level nested array",
    ),
    ArrayTestClass(
        id="nested_deep_not_found",
        value=[2, 3],
        array=[[1, [2, 3]], [4, 5]],
        expected=False,
        msg="Should not find array at wrong nesting level",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = NESTED_MIXED_ARRAY_TESTS + DEEPLY_NESTED_TESTS

TEST_SUBSET_FOR_LITERAL = [
    NESTED_MIXED_ARRAY_TESTS[0],  # nested_find_object_in_mixed
    DEEPLY_NESTED_TESTS[0],  # nested_3_levels
    DEEPLY_NESTED_TESTS[-1],  # nested_deep_not_found
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_in_literal(collection, test):
    """Test $in nested arrays with literal values."""
    result = execute_expression(collection, {"$in": [test.value, test.array]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_in_insert(collection, test):
    """Test $in nested arrays with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$in": ["$val", "$arr"]}, {"val": test.value, "arr": test.array}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
