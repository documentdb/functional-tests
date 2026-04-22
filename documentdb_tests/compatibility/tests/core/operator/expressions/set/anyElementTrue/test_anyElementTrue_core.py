"""
Tests for $anyElementTrue core behavior.

Covers mixed arrays, all-falsy/all-truthy combinations, empty/nested arrays,
BSON type distinction, shorthand syntax, boolean result type,
order independence, and argument handling.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.set.anyElementTrue.utils.anyElementTrue_utils import (  # noqa: E501
    AnyElementTrueTest,
    build_expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
)

ANYELEMENTTRUE_CORE_TESTS: list[AnyElementTrueTest] = [
    # --- All falsy combined ---
    AnyElementTrueTest(
        "false_0_null",
        array=[False, 0, None],
        expected=False,
        msg="Should return false when all elements are falsy",
    ),
    AnyElementTrueTest(
        "all_falsy_types",
        array=[False, 0, Int64(0), 0.0, Decimal128("0"), None],
        expected=False,
        msg="Should return false when all falsy types are combined",
    ),
    AnyElementTrueTest(
        "all_nulls",
        array=[None, None, None],
        expected=False,
        msg="Should return false when all elements are null",
    ),
    AnyElementTrueTest(
        "all_false",
        array=[False, False, False],
        expected=False,
        msg="Should return false when all elements are false",
    ),
    AnyElementTrueTest(
        "all_zeros",
        array=[0, 0, 0],
        expected=False,
        msg="Should return false when all elements are zero",
    ),
    # --- Mixed falsy and truthy ---
    AnyElementTrueTest(
        "false_true",
        array=[False, True],
        expected=True,
        msg="Should return true for one true among false",
    ),
    AnyElementTrueTest(
        "0_1", array=[0, 1], expected=True, msg="Should return true for one 1 among 0"
    ),
    AnyElementTrueTest(
        "null_hello",
        array=[None, "hello"],
        expected=True,
        msg="Should return true for string among null",
    ),
    AnyElementTrueTest(
        "falsy_plus_1",
        array=[False, 0, None, 1],
        expected=True,
        msg="Should return true for one truthy among many falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_empty_str",
        array=[False, 0, None, ""],
        expected=True,
        msg="Should return true for empty string among falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_empty_arr",
        array=[False, 0, None, []],
        expected=True,
        msg="Should return true for empty array among falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_empty_obj",
        array=[False, 0, None, {}],
        expected=True,
        msg="Should return true for empty object among falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_objectid",
        array=[False, 0, None, ObjectId("507f1f77bcf86cd799439011")],
        expected=True,
        msg="Should return true for ObjectId among falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_date",
        array=[False, 0, None, datetime(2017, 1, 1)],
        expected=True,
        msg="Should return true for date among falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_timestamp",
        array=[False, 0, None, Timestamp(0, 1)],
        expected=True,
        msg="Should return true for Timestamp among falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_bindata",
        array=[False, 0, None, Binary(b"", 0)],
        expected=True,
        msg="Should return true for BinData among falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_regex",
        array=[False, 0, None, Regex("regex")],
        expected=True,
        msg="Should return true for regex among falsy",
    ),
    AnyElementTrueTest(
        "falsy_plus_object",
        array=[False, 0, None, {"a": 1}],
        expected=True,
        msg="Should return true for object among falsy",
    ),
    AnyElementTrueTest(
        "all_falsy_plus_empty_str",
        array=[False, 0, Int64(0), 0.0, Decimal128("0"), None, ""],
        expected=True,
        msg="Should return true when empty string added to falsy",
    ),
    # --- Empty array and nested arrays ---
    AnyElementTrueTest(
        "empty_array", array=[], expected=False, msg="Should return false for empty array"
    ),
    AnyElementTrueTest(
        "nested_false",
        array=[[False]],
        expected=True,
        msg="Should return true for nested false element",
    ),
    AnyElementTrueTest(
        "nested_zero", array=[[0]], expected=True, msg="Should return true for nested zero element"
    ),
    AnyElementTrueTest(
        "nested_null",
        array=[[None]],
        expected=True,
        msg="Should return true for nested null element",
    ),
    AnyElementTrueTest(
        "nested_all_falsy",
        array=[[False, 0, None]],
        expected=True,
        msg="Should return true for nested array with all falsy",
    ),
    AnyElementTrueTest(
        "empty_arr_and_false",
        array=[[], False],
        expected=True,
        msg="Should return true for empty array element",
    ),
    AnyElementTrueTest(
        "nested_false_and_false",
        array=[[False], False],
        expected=True,
        msg="Should return true for nested false array element",
    ),
    AnyElementTrueTest(
        "multiple_nested",
        array=[[False], [0], [None]],
        expected=True,
        msg="Should return true for multiple nested arrays",
    ),
    AnyElementTrueTest(
        "deeply_nested_false",
        array=[[[[[[False]]]]]],
        expected=True,
        msg="Should return true for deeply nested false",
    ),
    AnyElementTrueTest(
        "deeply_nested_zero",
        array=[[[[[[0]]]]]],
        expected=True,
        msg="Should return true for deeply nested zero",
    ),
    AnyElementTrueTest(
        "deeply_nested_empty",
        array=[[[[[[]]]]]],
        expected=True,
        msg="Should return true for deeply nested empty",
    ),
    AnyElementTrueTest(
        "nested_nan",
        array=[[DECIMAL128_NAN]],
        expected=True,
        msg="Should return true for nested NaN array",
    ),
    AnyElementTrueTest(
        "nested_inf",
        array=[[FLOAT_INFINITY]],
        expected=True,
        msg="Should return true for nested Infinity array",
    ),
    AnyElementTrueTest(
        "mixed_nesting_depths",
        array=[[False], [[None]], [[[0]]]],
        expected=True,
        msg="Should return true for mixed nesting depths",
    ),
    # --- Order independence ---
    AnyElementTrueTest(
        "false_true_order",
        array=[False, True],
        expected=True,
        msg="Should return true regardless of element order",
    ),
    AnyElementTrueTest(
        "true_false_order",
        array=[True, False],
        expected=True,
        msg="Should return true regardless of reversed element order",
    ),
    AnyElementTrueTest(
        "0_1_null",
        array=[0, 1, None],
        expected=True,
        msg="Should return true when array has mixed falsy and truthy",
    ),
    AnyElementTrueTest(
        "null_0_1",
        array=[None, 0, 1],
        expected=True,
        msg="Should return true when truthy element is at end",
    ),
    AnyElementTrueTest(
        "1_null_0",
        array=[1, None, 0],
        expected=True,
        msg="Should return true when truthy element is at start",
    ),
    # --- BSON type distinction ---
    AnyElementTrueTest(
        "false_and_0", array=[False, 0], expected=False, msg="Should return false for false and 0"
    ),
    AnyElementTrueTest(
        "false_and_null",
        array=[False, None],
        expected=False,
        msg="Should return false for false and null",
    ),
    AnyElementTrueTest(
        "empty_str_and_null",
        array=["", None],
        expected=True,
        msg="Should return true for empty string with null",
    ),
    AnyElementTrueTest(
        "neg_zero_and_zero",
        array=[DOUBLE_NEGATIVE_ZERO, 0.0],
        expected=False,
        msg="Should return false for -0.0 and 0.0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ANYELEMENTTRUE_CORE_TESTS))
def test_anyElementTrue_core(collection, test):
    """Test $anyElementTrue core behavior with literal arrays."""
    result = execute_expression(collection, build_expr(test))
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Boolean result type verification
# ---------------------------------------------------------------------------
def test_anyElementTrue_returns_boolean_true(collection):
    """Test $anyElementTrue returns exactly boolean true, not 1."""
    result = execute_expression(collection, {"$anyElementTrue": [[True]]})
    assert_expression_result(result, expected=True, msg="Should return boolean true")


def test_anyElementTrue_returns_boolean_false(collection):
    """Test $anyElementTrue returns exactly boolean false, not 0."""
    result = execute_expression(collection, {"$anyElementTrue": [[False]]})
    assert_expression_result(result, expected=False, msg="Should return boolean false")


def test_anyElementTrue_empty_returns_boolean_false(collection):
    """Test $anyElementTrue on empty array returns exactly boolean false."""
    result = execute_expression(collection, {"$anyElementTrue": [[]]})
    assert_expression_result(result, expected=False, msg="Empty array should return boolean false")


# ---------------------------------------------------------------------------
# Shorthand syntax
# ---------------------------------------------------------------------------
def test_anyElementTrue_shorthand_field(collection):
    """Test $anyElementTrue shorthand syntax without outer array wrapper."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": "$arr"}, {"arr": [True, False]}
    )
    assert_expression_result(result, expected=True, msg="Shorthand syntax should work")


def test_anyElementTrue_shorthand_field_all_falsy(collection):
    """Test $anyElementTrue shorthand syntax with all falsy array."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": "$arr"}, {"arr": [0, False]}
    )
    assert_expression_result(
        result, expected=False, msg="Shorthand with all falsy should return false"
    )


# ---------------------------------------------------------------------------
# Argument handling
# ---------------------------------------------------------------------------
def test_anyElementTrue_single_arg_literal(collection):
    """Test $anyElementTrue with single literal array argument."""
    result = execute_expression(collection, {"$anyElementTrue": [[True, False]]})
    assert_expression_result(result, expected=True, msg="Single literal array argument should work")


def test_anyElementTrue_single_arg_field(collection):
    """Test $anyElementTrue with single field path argument."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$arr"]}, {"arr": [True]}
    )
    assert_expression_result(result, expected=True, msg="Single field path argument should work")


# ---------------------------------------------------------------------------
# Field path resolution
# ---------------------------------------------------------------------------
def test_anyElementTrue_field_all_true(collection):
    """Test $anyElementTrue with field path resolving to all-true array."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$arr"]}, {"arr": [True, True]}
    )
    assert_expression_result(result, expected=True, msg="All true field should return true")


def test_anyElementTrue_field_some_true(collection):
    """Test $anyElementTrue with field path resolving to mixed array."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$arr"]}, {"arr": [True, False]}
    )
    assert_expression_result(result, expected=True, msg="Some true field should return true")


def test_anyElementTrue_field_none_true(collection):
    """Test $anyElementTrue with field path resolving to all-false array."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$arr"]}, {"arr": [0, False]}
    )
    assert_expression_result(result, expected=False, msg="None true field should return false")


def test_anyElementTrue_field_null_input(collection):
    """Test $anyElementTrue with field containing [null]."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$arr"]}, {"arr": [None]}
    )
    assert_expression_result(
        result, expected=False, msg="Should return false for array with only null"
    )


def test_anyElementTrue_field_null_true(collection):
    """Test $anyElementTrue with field containing [null, true]."""
    result = execute_expression_with_insert(
        collection, {"$anyElementTrue": ["$arr"]}, {"arr": [None, True]}
    )
    assert_expression_result(
        result, expected=True, msg="Should return true for array with null and true"
    )


def test_anyElementTrue_field_empty(collection):
    """Test $anyElementTrue with field containing empty array."""
    result = execute_expression_with_insert(collection, {"$anyElementTrue": ["$arr"]}, {"arr": []})
    assert_expression_result(result, expected=False, msg="Empty array field should return false")
