"""
Core behavior tests for $zip expression.

Tests zipping arrays of various element types, equal/unequal lengths,
useLongestLength, defaults, empty arrays, single arrays, nested arrays,
null propagation, and large arrays.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Success: basic zipping — equal length arrays
# Property [Basic Transform]: $map applies an expression to each element.
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

# Success: empty and single element
DEGENERATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="both_empty",
        doc={"arr0": [], "arr1": []},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[],
        msg="Should return empty for two empty arrays",
    ),
    ExpressionTestCase(
        id="three_empty",
        doc={"arr0": [], "arr1": [], "arr2": []},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        expected=[],
        msg="Three empty arrays return []",
    ),
    ExpressionTestCase(
        id="single_empty",
        doc={"arr0": []},
        expression={"$zip": {"inputs": ["$arr0"]}},
        expected=[],
        msg="Single empty array returns []",
    ),
    ExpressionTestCase(
        id="single_element_each",
        doc={"arr0": [1], "arr1": [10]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10]],
        msg="Should zip single-element arrays",
    ),
    ExpressionTestCase(
        id="single_input_array",
        doc={"arr0": [1, 2, 3]},
        expression={"$zip": {"inputs": ["$arr0"]}},
        expected=[[1], [2], [3]],
        msg="Single input should wrap each element",
    ),
    ExpressionTestCase(
        id="all_single_element_three",
        doc={"arr0": [1], "arr1": ["a"], "arr2": [True]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        expected=[[1, "a", True]],
        msg="All single-element arrays produce one row",
    ),
    ExpressionTestCase(
        id="empty_with_longest_false",
        doc={"arr0": [], "arr1": [1, 2, 3]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[],
        msg="Empty array with shortest length returns []",
    ),
    ExpressionTestCase(
        id="empty_with_longest_true",
        doc={"arr0": [], "arr1": [1, 2, 3]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True}},
        expected=[[None, 1], [None, 2], [None, 3]],
        msg="Empty array with longest length pads with null",
    ),
    ExpressionTestCase(
        id="two_empty_longest_true",
        doc={"arr0": [], "arr1": []},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True}},
        expected=[],
        msg="Two empty arrays with longest length return []",
    ),
]

# Success: nested arrays as elements
# Property [Nested Arrays]: $map operates on nested array structures.
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_arrays",
        doc={"arr0": [[1, 2], [3, 4]], "arr1": ["a", "b"]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[[1, 2], "a"], [[3, 4], "b"]],
        msg="Should zip nested arrays as elements",
    ),
    ExpressionTestCase(
        id="objects_as_elements",
        doc={"arr0": [{"x": 1}, {"x": 2}], "arr1": [{"y": 10}, {"y": 20}]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[{"x": 1}, {"y": 10}], [{"x": 2}, {"y": 20}]],
        msg="Objects preserved as elements",
    ),
    ExpressionTestCase(
        id="mixed_types_six",
        doc={"arr0": [1, "a", None, True, {"k": 1}, [9]], "arr1": [10, 20, 30, 40, 50, 60]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10], ["a", 20], [None, 30], [True, 40], [{"k": 1}, 50], [[9], 60]],
        msg="Mixed types preserved in transposition",
    ),
]

# Success: null propagation
NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="null_first_input",
        doc={"arr0": None, "arr1": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=None,
        msg="Should return null when first input is null",
    ),
    ExpressionTestCase(
        id="null_second_input",
        doc={"arr0": [1, 2], "arr1": None},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=None,
        msg="Should return null when second input is null",
    ),
    ExpressionTestCase(
        id="all_null_inputs",
        doc={"arr0": None, "arr1": None},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=None,
        msg="Should return null when all inputs are null",
    ),
    ExpressionTestCase(
        id="null_elements_in_arrays",
        doc={"arr0": [1, None], "arr1": [None, 2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, None], [None, 2]],
        msg="Should preserve null elements within arrays",
    ),
]

# Success: objects as elements
OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="arrays_of_objects",
        doc={"arr0": [{"a": 1}], "arr1": [{"b": 2}]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[{"a": 1}, {"b": 2}]],
        msg="Should zip arrays of objects",
    ),
]

# Success: large arrays
# Property [Large Arrays]: $map handles large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="large_arrays",
        doc={"arr0": list(range(1000)), "arr1": list(range(1000, 2000))},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[i, i + 1000] for i in range(1000)],
        msg="Should zip large arrays",
    ),
]

# Success: many input arrays
MANY_INPUTS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="ten_inputs",
        doc={f"arr{i}": [i] for i in range(10)},
        expression={"$zip": {"inputs": [f"$arr{i}" for i in range(10)]}},
        expected=[list(range(10))],
        msg="Ten inputs transpose correctly",
    ),
    ExpressionTestCase(
        id="fifty_inputs",
        doc={f"arr{i}": [i] for i in range(50)},
        expression={"$zip": {"inputs": [f"$arr{i}" for i in range(50)]}},
        expected=[list(range(50))],
        msg="50 single-element inputs produce one 50-element row",
    ),
]

# Success: multiple arrays of different lengths
MULTI_LENGTH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="three_arrays_shortest",
        doc={"arr0": [1], "arr1": [10, 20, 30], "arr2": [100, 200, 300, 400, 500]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        expected=[[1, 10, 100]],
        msg="Three arrays shortest = 1",
    ),
    ExpressionTestCase(
        id="three_arrays_longest_no_defaults",
        doc={"arr0": [1], "arr1": [10, 20, 30], "arr2": [100, 200, 300, 400, 500]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"], "useLongestLength": True}},
        expected=[
            [1, 10, 100],
            [None, 20, 200],
            [None, 30, 300],
            [None, None, 400],
            [None, None, 500],
        ],
        msg="Three arrays longest pads with null",
    ),
    ExpressionTestCase(
        id="three_arrays_longest_with_defaults",
        doc={"arr0": [1], "arr1": [10, 20, 30], "arr2": [100, 200, 300, 400, 500]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1", "$arr2"],
                "useLongestLength": True,
                "defaults": [0, "x", False],
            }
        },
        expected=[[1, 10, 100], [0, 20, 200], [0, 30, 300], [0, "x", 400], [0, "x", 500]],
        msg="Three arrays longest with defaults",
    ),
    ExpressionTestCase(
        id="four_arrays_two_empty",
        doc={"arr0": [], "arr1": [], "arr2": [1, 2], "arr3": [3, 4, 5]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1", "$arr2", "$arr3"], "useLongestLength": True}
        },
        expected=[[None, None, 1, 3], [None, None, 2, 4], [None, None, None, 5]],
        msg="Four arrays two empty with longest",
    ),
]

# Aggregate and test
ALL_TESTS = (
    BASIC_TESTS
    + UNEQUAL_LENGTH_TESTS
    + USE_LONGEST_TESTS
    + DEFAULTS_TESTS
    + DEGENERATE_TESTS
    + NESTED_ARRAY_TESTS
    + NULL_TESTS
    + OBJECT_TESTS
    + LARGE_ARRAY_TESTS
    + MANY_INPUTS_TESTS
    + MULTI_LENGTH_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_zip_insert(collection, test):
    """Test $zip with values from inserted documents."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
