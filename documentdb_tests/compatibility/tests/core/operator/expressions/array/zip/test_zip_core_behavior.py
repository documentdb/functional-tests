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

# Success: basic zipping — equal length arrays
# Property [Basic Transform]: $zip transposes arrays element-wise.
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="two_int_arrays",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20, 30]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10], [2, 20], [3, 30]],
        msg="Should zip two int arrays",
    ),
    ExpressionTestCase(
        id="two_string_arrays",
        doc={"arr0": ["a", "b"], "arr1": ["c", "d"]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[["a", "c"], ["b", "d"]],
        msg="Should zip two string arrays",
    ),
    ExpressionTestCase(
        id="three_arrays",
        doc={"arr0": [1, 2], "arr1": [10, 20], "arr2": [100, 200]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        expected=[[1, 10, 100], [2, 20, 200]],
        msg="Should zip three arrays",
    ),
    ExpressionTestCase(
        id="mixed_type_elements",
        doc={"arr0": [1, "two"], "arr1": [True, None]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, True], ["two", None]],
        msg="Should zip arrays with mixed types",
    ),
    ExpressionTestCase(
        id="numeric_cross_types",
        doc={"arr0": [1, Int64(2)], "arr1": [3.0, Decimal128("4")]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 3.0], [Int64(2), Decimal128("4")]],
        msg="Should zip mixed numeric type arrays",
    ),
]

# Success: unequal length — truncate to shortest (default)
# Property [Unequal Length]: $zip truncates to the shortest array.
UNEQUAL_LENGTH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="first_shorter",
        doc={"arr0": [1, 2], "arr1": [10, 20, 30]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10], [2, 20]],
        msg="Should truncate to shorter first array",
    ),
    ExpressionTestCase(
        id="second_shorter",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10], [2, 20]],
        msg="Should truncate to shorter second array",
    ),
    ExpressionTestCase(
        id="one_empty",
        doc={"arr0": [], "arr1": [1, 2, 3]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[],
        msg="Empty array should produce empty result",
    ),
]

# Success: useLongestLength
USE_LONGEST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="longest_pads_null",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True}},
        expected=[[1, 10], [2, 20], [3, None]],
        msg="Should pad shorter array with null",
    ),
    ExpressionTestCase(
        id="longest_both_short",
        doc={"arr0": [1], "arr1": [10, 20], "arr2": [100, 200, 300]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"], "useLongestLength": True}},
        expected=[[1, 10, 100], [None, 20, 200], [None, None, 300]],
        msg="Should pad multiple shorter arrays with null",
    ),
    ExpressionTestCase(
        id="longest_equal_length",
        doc={"arr0": [1, 2], "arr1": [10, 20]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True}},
        expected=[[1, 10], [2, 20]],
        msg="Equal length with useLongestLength should behave same",
    ),
    ExpressionTestCase(
        id="longest_false_truncates",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": False}},
        expected=[[1, 10], [2, 20]],
        msg="useLongestLength false should truncate",
    ),
]

# Success: defaults
# Property [Defaults]: $zip pads shorter arrays with default values.
DEFAULTS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="defaults_fill_shorter",
        doc={"arr0": [1, 2, 3], "arr1": [10, 20]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, 0]}
        },
        expected=[[1, 10], [2, 20], [3, 0]],
        msg="Should fill shorter array with default value",
    ),
    ExpressionTestCase(
        id="defaults_multiple_arrays",
        doc={"arr0": [1], "arr1": [10, 20], "arr2": [100, 200, 300]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1", "$arr2"],
                "useLongestLength": True,
                "defaults": [-1, -2, -3],
            }
        },
        expected=[[1, 10, 100], [-1, 20, 200], [-1, -2, 300]],
        msg="Should fill multiple shorter arrays with respective defaults",
    ),
    ExpressionTestCase(
        id="defaults_null_value",
        doc={"arr0": [1, 2, 3], "arr1": [10]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [None, None],
            }
        },
        expected=[[1, 10], [2, None], [3, None]],
        msg="Null defaults should work same as no defaults",
    ),
    ExpressionTestCase(
        id="defaults_string",
        doc={"arr0": [1, 2, 3], "arr1": ["a"]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, "missing"],
            }
        },
        expected=[[1, "a"], [2, "missing"], [3, "missing"]],
        msg="Should use string default value",
    ),
    ExpressionTestCase(
        id="defaults_not_used_equal_length",
        doc={"arr0": [1, 2], "arr1": [10, 20]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, 0]}
        },
        expected=[[1, 10], [2, 20]],
        msg="Defaults not used when arrays are equal length",
    ),
    ExpressionTestCase(
        id="defaults_falsy_empty_string",
        doc={"arr0": [1, 2], "arr1": ["a"]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, ""]}
        },
        expected=[[1, "a"], [2, ""]],
        msg="Falsy defaults (empty string) used correctly",
    ),
    ExpressionTestCase(
        id="defaults_false",
        doc={"arr0": [1, 2], "arr1": ["a"]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True, "defaults": [0, False]}
        },
        expected=[[1, "a"], [2, False]],
        msg="False default used correctly",
    ),
    ExpressionTestCase(
        id="defaults_complex_types",
        doc={"arr0": [1, 2], "arr1": ["a"]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [{"x": 1}, [1, 2]],
            }
        },
        expected=[[1, "a"], [2, [1, 2]]],
        msg="Complex type defaults used correctly",
    ),
    ExpressionTestCase(
        id="defaults_nested_array",
        doc={"arr0": [1, 2], "arr1": ["a"]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [[1, 2], "fallback"],
            }
        },
        expected=[[1, "a"], [2, "fallback"]],
        msg="Nested array default used as-is",
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
