"""
Tests for $allElementsTrue core behavior.

Covers mixed arrays, nested array behavior (does not descend),
element order independence, falsy position testing, scale testing,
large mixed-type arrays, falsy position testing, and scale testing.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.set.allElementsTrue.utils.allElementsTrue_utils import (  # noqa: E501
    AllElementsTrueTest,
    build_expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

_LARGE_TRUTHY = [
    True,
    1,
    Int64(1),
    1.5,
    Decimal128("1"),
    "str",
    {"a": 1},
    [1],
    ObjectId("507f1f77bcf86cd799439011"),
    datetime(2017, 1, 1),
    Timestamp(1, 1),
    Binary(b"", 0),
    Regex("re"),
]

ALL_ELEMENTS_TRUE_CORE_TESTS: list[AllElementsTrueTest] = [
    # --- Mixed arrays — all truthy ---
    AllElementsTrueTest(
        "true_1_string",
        array=[True, 1, "someString"],
        expected=True,
        msg="Should return true for mixed truthy types",
    ),
    AllElementsTrueTest(
        "true_seven",
        array=[True, "seven"],
        expected=True,
        msg="Should return true for bool and string",
    ),
    AllElementsTrueTest(
        "all_numeric_nonzero",
        array=[1, Int64(2), 3.5, Decimal128("4")],
        expected=True,
        msg="Should return true for all non-zero numerics",
    ),
    AllElementsTrueTest(
        "mixed_bson_truthy",
        array=[
            True,
            1,
            Int64(1),
            1.5,
            Decimal128("1"),
            "str",
            {"a": 1},
            [1],
            ObjectId("507f1f77bcf86cd799439011"),
            datetime(2017, 1, 1),
            Timestamp(1, 1),
            Binary(b"", 0),
            Regex("re"),
        ],
        expected=True,
        msg="Should return true for all BSON truthy types",
    ),
    # --- Mixed truthy and falsy — returns false ---
    AllElementsTrueTest(
        "true_false",
        array=[True, False],
        expected=False,
        msg="Should return false for true and false",
    ),
    AllElementsTrueTest("1_0", array=[1, 0], expected=False, msg="Should return false for 1 and 0"),
    AllElementsTrueTest(
        "true_null", array=[True, None], expected=False, msg="Should return false for true and null"
    ),
    AllElementsTrueTest(
        "hello_0_true",
        array=["hello", 0, True],
        expected=False,
        msg="Should return false for string with zero",
    ),
    AllElementsTrueTest(
        "null_false_0",
        array=[None, False, 0],
        expected=False,
        msg="Should return false when all elements are falsy",
    ),
    # --- Single falsy among many truthy ---
    AllElementsTrueTest(
        "false_at_end",
        array=[True, 1, "a", {}, [], False],
        expected=False,
        msg="Should return false when false is at end",
    ),
    AllElementsTrueTest(
        "null_at_end",
        array=[True, 1, "a", {}, [], None],
        expected=False,
        msg="Should return false when null is at end",
    ),
    AllElementsTrueTest(
        "zero_at_end",
        array=[True, 1, "a", {}, [], 0],
        expected=False,
        msg="Should return false when zero is at end",
    ),
    # --- Large mixed-type array ---
    AllElementsTrueTest(
        "all_truthy_large",
        array=_LARGE_TRUTHY,
        expected=True,
        msg="Should return true for large all-truthy array",
    ),
    AllElementsTrueTest(
        "plus_false",
        array=_LARGE_TRUTHY + [False],
        expected=False,
        msg="Should return false for large array with false appended",
    ),
    AllElementsTrueTest(
        "plus_null",
        array=_LARGE_TRUTHY + [None],
        expected=False,
        msg="Should return false for large array with null appended",
    ),
    AllElementsTrueTest(
        "plus_zero",
        array=_LARGE_TRUTHY + [0],
        expected=False,
        msg="Should return false for large array with zero appended",
    ),
    # --- Nested array behavior — does NOT descend ---
    AllElementsTrueTest(
        "nested_false",
        array=[[False]],
        expected=True,
        msg="Should return true for nested false element",
    ),
    AllElementsTrueTest(
        "nested_zero", array=[[0]], expected=True, msg="Should return true for nested zero element"
    ),
    AllElementsTrueTest(
        "nested_null",
        array=[[None]],
        expected=True,
        msg="Should return true for nested null element",
    ),
    AllElementsTrueTest(
        "nested_empty",
        array=[[]],
        expected=True,
        msg="Should return true for nested empty array element",
    ),
    AllElementsTrueTest(
        "nested_all_falsy",
        array=[[False, 0, None]],
        expected=True,
        msg="Should return true for nested array with all falsy",
    ),
    AllElementsTrueTest(
        "two_nested_arrays",
        array=[[True], [False]],
        expected=True,
        msg="Should return true for two nested arrays",
    ),
    AllElementsTrueTest(
        "two_empty_nested",
        array=[[], []],
        expected=True,
        msg="Should return true for two empty nested arrays",
    ),
    AllElementsTrueTest(
        "deeply_nested",
        array=[[[[False]]]],
        expected=True,
        msg="Should return true for deeply nested false",
    ),
    AllElementsTrueTest(
        "deeply_nested_zero",
        array=[[[[[[0]]]]]],
        expected=True,
        msg="Should return true for deeply nested 0",
    ),
    AllElementsTrueTest(
        "mixed_nesting_depths",
        array=[[False], [[None]], [[[0]]]],
        expected=True,
        msg="Should return true for mixed nesting depths",
    ),
    # --- Element order independence ---
    AllElementsTrueTest(
        "true_1_string_order1",
        array=[True, 1, "string"],
        expected=True,
        msg="Should return true for order 1",
    ),
    AllElementsTrueTest(
        "true_1_string_order2",
        array=[1, "string", True],
        expected=True,
        msg="Should return true for order 2",
    ),
    AllElementsTrueTest(
        "false_1_string_order1",
        array=[False, 1, "string"],
        expected=False,
        msg="Should return false for order 1 with false",
    ),
    AllElementsTrueTest(
        "false_1_string_order2",
        array=[1, "string", False],
        expected=False,
        msg="Should return false for order 2 with false",
    ),
    # --- Comparison with $anyElementTrue — allElementsTrue side ---
    AllElementsTrueTest(
        "cmp_empty", array=[], expected=True, msg="Should return true for empty array"
    ),
    AllElementsTrueTest(
        "cmp_true_only",
        array=[True],
        expected=True,
        msg="Should return true for single true element",
    ),
    AllElementsTrueTest(
        "cmp_false_only",
        array=[False],
        expected=False,
        msg="Should return false for single false element",
    ),
    AllElementsTrueTest(
        "cmp_true_false",
        array=[True, False],
        expected=False,
        msg="Should return false for true and false elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_ELEMENTS_TRUE_CORE_TESTS))
def test_allElementsTrue_core(collection, test):
    """Test $allElementsTrue core behavior with literal arrays."""
    result = execute_expression(collection, build_expr(test))
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Nested arrays via field reference (requires insert)
# ---------------------------------------------------------------------------
def test_allElementsTrue_field_array_of_arrays_all_truthy(collection):
    """Test $allElementsTrue with field containing array of arrays — all truthy as elements."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$arr"]}, {"arr": [[True], [False], [None]]}
    )
    assert_expression_result(
        result, expected=True, msg="Should return true when each element is an array"
    )


def test_allElementsTrue_field_array_with_bare_false(collection):
    """Test $allElementsTrue with field containing array with bare false element."""
    result = execute_expression_with_insert(
        collection, {"$allElementsTrue": ["$arr"]}, {"arr": [[True], False]}
    )
    assert_expression_result(
        result, expected=False, msg="Should return false when array contains bare false element"
    )


# ---------------------------------------------------------------------------
# Boolean result type verification
# ---------------------------------------------------------------------------
def test_allElementsTrue_returns_boolean_true(collection):
    """Test $allElementsTrue returns exactly boolean true, not 1."""
    result = execute_expression(collection, {"$allElementsTrue": [[True]]})
    assert_expression_result(result, expected=True, msg="Should return boolean true")


def test_allElementsTrue_returns_boolean_false(collection):
    """Test $allElementsTrue returns exactly boolean false, not 0."""
    result = execute_expression(collection, {"$allElementsTrue": [[False]]})
    assert_expression_result(result, expected=False, msg="Should return boolean false")


def test_allElementsTrue_empty_returns_boolean_true(collection):
    """Test $allElementsTrue on empty array returns exactly boolean true."""
    result = execute_expression(collection, {"$allElementsTrue": [[]]})
    assert_expression_result(result, expected=True, msg="Empty array should return boolean true")
