"""
Core behavior tests for $zip expression.

Tests zipping arrays of various element types, equal/unequal lengths,
useLongestLength, and defaults.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Basic Transform]: $zip transposes arrays element-wise.
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "two_int_arrays",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20, 30]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10], [2, 20], [3, 30]],
        msg="$zip should zip two int arrays",
    ),
    ExpressionTestCase(
        "two_string_arrays",
        doc={"arr0": ["a", "b"], "arr1": ["c", "d"]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[["a", "c"], ["b", "d"]],
        msg="$zip should zip two string arrays",
    ),
    ExpressionTestCase(
        "three_arrays",
        doc={"arr0": [1, 2], "arr1": [10, 20], "arr2": [100, 200]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        expected=[[1, 10, 100], [2, 20, 200]],
        msg="$zip should zip three arrays",
    ),
    ExpressionTestCase(
        "mixed_type_elements",
        doc={"arr0": [1, "two"], "arr1": [True, None]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, True], ["two", None]],
        msg="$zip should zip arrays with mixed types",
    ),
    ExpressionTestCase(
        "numeric_cross_types",
        doc={"arr0": [1, Int64(2)], "arr1": [3.0, Decimal128("4")]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 3.0], [Int64(2), Decimal128("4")]],
        msg="$zip should zip mixed numeric type arrays",
    ),
]

# Property [Unequal Length]: $zip truncates to the shortest array.
UNEQUAL_LENGTH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_shorter",
        doc={"arr0": [1, 2], "arr1": [10, 20, 30]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10], [2, 20]],
        msg="$zip should truncate to shorter first array",
    ),
    ExpressionTestCase(
        "second_shorter",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10], [2, 20]],
        msg="$zip should truncate to shorter second array",
    ),
    ExpressionTestCase(
        "one_empty",
        doc={"arr0": [], "arr1": [1, 2, 3]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[],
        msg="$zip empty array should produce empty result",
    ),
]

# Property [Longest Length]: $zip pads to longest array when useLongestLength is true.
USE_LONGEST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "longest_pads_null",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True}},
        expected=[[1, 10], [2, 20], [3, None]],
        msg="$zip should pad shorter array with null",
    ),
    ExpressionTestCase(
        "longest_both_short",
        doc={"arr0": [1], "arr1": [10, 20], "arr2": [100, 200, 300]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"], "useLongestLength": True}},
        expected=[[1, 10, 100], [None, 20, 200], [None, None, 300]],
        msg="$zip should pad multiple shorter arrays with null",
    ),
    ExpressionTestCase(
        "longest_equal_length",
        doc={"arr0": [1, 2], "arr1": [10, 20]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True}},
        expected=[[1, 10], [2, 20]],
        msg="$zip equal length with useLongestLength should behave same",
    ),
    ExpressionTestCase(
        "longest_false_truncates",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": False}},
        expected=[[1, 10], [2, 20]],
        msg="$zip useLongestLength false should truncate",
    ),
]

# Property [Defaults]: $zip pads shorter arrays with default values.
DEFAULTS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "defaults_fill_shorter",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, 0]}
        },
        expected=[[1, 10], [2, 20], [3, 0]],
        msg="$zip should fill shorter array with default value",
    ),
    ExpressionTestCase(
        "defaults_multiple_arrays",
        doc={"arr0": [1], "arr1": [10, 20], "arr2": [100, 200, 300]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1", "$arr2"],
                "useLongestLength": True,
                "defaults": [-1, -2, -3],
            }
        },
        expected=[[1, 10, 100], [-1, 20, 200], [-1, -2, 300]],
        msg="$zip should fill multiple shorter arrays with respective defaults",
    ),
    ExpressionTestCase(
        "defaults_null_value",
        doc={"arr0": [1, 2, 3], "arr1": [10]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [None, None],
            }
        },
        expected=[[1, 10], [2, None], [3, None]],
        msg="$zip null defaults should work same as no defaults",
    ),
    ExpressionTestCase(
        "defaults_string",
        doc={"arr0": [1, 2, 3], "arr1": ["a"]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, "missing"],
            }
        },
        expected=[[1, "a"], [2, "missing"], [3, "missing"]],
        msg="$zip should use string default value",
    ),
    ExpressionTestCase(
        "defaults_not_used_equal_length",
        doc={"arr0": [1, 2], "arr1": [10, 20]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, 0]}
        },
        expected=[[1, 10], [2, 20]],
        msg="$zip defaults not used when arrays are equal length",
    ),
    ExpressionTestCase(
        "defaults_falsy_empty_string",
        doc={"arr0": [1, 2], "arr1": ["a"]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, ""]}
        },
        expected=[[1, "a"], [2, ""]],
        msg="$zip falsy defaults (empty string) used correctly",
    ),
    ExpressionTestCase(
        "defaults_false",
        doc={"arr0": [1, 2], "arr1": ["a"]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, False]}
        },
        expected=[[1, "a"], [2, False]],
        msg="$zip false default used correctly",
    ),
    ExpressionTestCase(
        "defaults_complex_types",
        doc={"arr0": [1, 2], "arr1": ["a"]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [{"x": 1}, [1, 2]],
            }
        },
        expected=[[1, "a"], [2, [1, 2]]],
        msg="$zip complex type defaults used correctly",
    ),
    ExpressionTestCase(
        "defaults_nested_array",
        doc={"arr0": [1, 2], "arr1": ["a"]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [[1, 2], "fallback"],
            }
        },
        expected=[[1, "a"], [2, "fallback"]],
        msg="$zip nested array default used as-is",
    ),
]

ALL_TESTS = BASIC_TESTS + UNEQUAL_LENGTH_TESTS + USE_LONGEST_TESTS + DEFAULTS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_zip_core_behavior(collection, test):
    """Test $zip core behavior: basic zipping, unequal lengths, useLongestLength, defaults."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
