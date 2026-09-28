"""
Degenerate and edge case tests for $zip expression.

Tests empty arrays, single arrays, nested arrays, null propagation,
objects as elements, large arrays, many inputs, and multi-length arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Empty/Single]: $zip handles empty arrays and single-element arrays.
DEGENERATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "both_empty",
        doc={"arr0": [], "arr1": []},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[],
        msg="$zip should return empty for two empty arrays",
    ),
    ExpressionTestCase(
        "three_empty",
        doc={"arr0": [], "arr1": [], "arr2": []},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        expected=[],
        msg="$zip three empty arrays return []",
    ),
    ExpressionTestCase(
        "single_empty",
        doc={"arr0": []},
        expression={"$zip": {"inputs": ["$arr0"]}},
        expected=[],
        msg="$zip single empty array returns []",
    ),
    ExpressionTestCase(
        "single_element_each",
        doc={"arr0": [1], "arr1": [10]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10]],
        msg="$zip should zip single-element arrays",
    ),
    ExpressionTestCase(
        "single_input_array",
        doc={"arr0": [1, 2, 3]},
        expression={"$zip": {"inputs": ["$arr0"]}},
        expected=[[1], [2], [3]],
        msg="$zip single input should wrap each element",
    ),
    ExpressionTestCase(
        "all_single_element_three",
        doc={"arr0": [1], "arr1": ["a"], "arr2": [True]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        expected=[[1, "a", True]],
        msg="$zip all single-element arrays produce one row",
    ),
    ExpressionTestCase(
        "empty_with_longest_true",
        doc={"arr0": [], "arr1": [1, 2, 3]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True}},
        expected=[[None, 1], [None, 2], [None, 3]],
        msg="$zip empty array with longest length pads with null",
    ),
    ExpressionTestCase(
        "two_empty_longest_true",
        doc={"arr0": [], "arr1": []},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"], "useLongestLength": True}},
        expected=[],
        msg="$zip two empty arrays with longest length return []",
    ),
]

# Property [Nested Arrays]: $zip preserves nested array and object elements.
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_arrays",
        doc={"arr0": [[1, 2], [3, 4]], "arr1": ["a", "b"]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[[1, 2], "a"], [[3, 4], "b"]],
        msg="$zip should zip nested arrays as elements",
    ),
    ExpressionTestCase(
        "objects_as_elements",
        doc={"arr0": [{"x": 1}, {"x": 2}], "arr1": [{"y": 10}, {"y": 20}]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[{"x": 1}, {"y": 10}], [{"x": 2}, {"y": 20}]],
        msg="$zip objects preserved as elements",
    ),
    ExpressionTestCase(
        "mixed_types_six",
        doc={"arr0": [1, "a", None, True, {"k": 1}, [9]], "arr1": [10, 20, 30, 40, 50, 60]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, 10], ["a", 20], [None, 30], [True, 40], [{"k": 1}, 50], [[9], 60]],
        msg="$zip mixed types preserved in transposition",
    ),
]

# Property [Null Propagation]: $zip returns null when any input array is null.
NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first_input",
        doc={"arr0": None, "arr1": [1, 2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=None,
        msg="$zip should return null when first input is null",
    ),
    ExpressionTestCase(
        "null_second_input",
        doc={"arr0": [1, 2], "arr1": None},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=None,
        msg="$zip should return null when second input is null",
    ),
    ExpressionTestCase(
        "all_null_inputs",
        doc={"arr0": None, "arr1": None},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=None,
        msg="$zip should return null when all inputs are null",
    ),
    ExpressionTestCase(
        "null_elements_in_arrays",
        doc={"arr0": [1, None], "arr1": [None, 2]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, None], [None, 2]],
        msg="$zip should preserve null elements within arrays",
    ),
]

# Property [Object Elements]: $zip preserves object elements within arrays.
OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arrays_of_objects",
        doc={"arr0": [{"a": 1}], "arr1": [{"b": 2}]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[{"a": 1}, {"b": 2}]],
        msg="$zip should zip arrays of objects",
    ),
]

# Property [Large Arrays]: $zip handles large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_arrays",
        doc={"arr0": list(range(1000)), "arr1": list(range(1000, 2000))},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[i, i + 1000] for i in range(1000)],
        msg="$zip should zip large arrays",
    ),
]

# Property [Many Inputs]: $zip handles many input arrays.
MANY_INPUTS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ten_inputs",
        doc={f"arr{i}": [i] for i in range(10)},
        expression={"$zip": {"inputs": [f"$arr{i}" for i in range(10)]}},
        expected=[list(range(10))],
        msg="$zip ten inputs transpose correctly",
    ),
    ExpressionTestCase(
        "fifty_inputs",
        doc={f"arr{i}": [i] for i in range(50)},
        expression={"$zip": {"inputs": [f"$arr{i}" for i in range(50)]}},
        expected=[list(range(50))],
        msg="$zip 50 single-element inputs produce one 50-element row",
    ),
]

# Property [Multi-Length]: $zip handles multiple arrays of varying lengths.
MULTI_LENGTH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "three_arrays_shortest",
        doc={"arr0": [1], "arr1": [10, 20, 30], "arr2": [100, 200, 300, 400, 500]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"]}},
        expected=[[1, 10, 100]],
        msg="$zip three arrays shortest = 1",
    ),
    ExpressionTestCase(
        "three_arrays_longest_no_defaults",
        doc={"arr0": [1], "arr1": [10, 20, 30], "arr2": [100, 200, 300, 400, 500]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1", "$arr2"], "useLongestLength": True}},
        expected=[
            [1, 10, 100],
            [None, 20, 200],
            [None, 30, 300],
            [None, None, 400],
            [None, None, 500],
        ],
        msg="$zip three arrays longest pads with null",
    ),
    ExpressionTestCase(
        "three_arrays_longest_with_defaults",
        doc={"arr0": [1], "arr1": [10, 20, 30], "arr2": [100, 200, 300, 400, 500]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1", "$arr2"],
                "useLongestLength": True,
                "defaults": [0, "x", False],
            }
        },
        expected=[[1, 10, 100], [0, 20, 200], [0, 30, 300], [0, "x", 400], [0, "x", 500]],
        msg="$zip three arrays longest with defaults",
    ),
    ExpressionTestCase(
        "four_arrays_two_empty",
        doc={"arr0": [], "arr1": [], "arr2": [1, 2], "arr3": [3, 4, 5]},
        expression={
            "$zip": {"inputs": ["$arr0", "$arr1", "$arr2", "$arr3"], "useLongestLength": True}
        },
        expected=[[None, None, 1, 3], [None, None, 2, 4], [None, None, None, 5]],
        msg="$zip four arrays two empty with longest",
    ),
]

ALL_TESTS = (
    DEGENERATE_TESTS
    + NESTED_ARRAY_TESTS
    + NULL_TESTS
    + OBJECT_TESTS
    + LARGE_ARRAY_TESTS
    + MANY_INPUTS_TESTS
    + MULTI_LENGTH_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_zip_edge_cases(collection, test):
    """Test $zip with empty, single, nested, null, large, and multi-length inputs."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
