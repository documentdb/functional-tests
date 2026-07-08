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
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

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
# Property [Nested Arrays]: $zip operates on nested array structures.
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
# Property [Large Arrays]: $zip handles large arrays.
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
def test_zip_degenerate(collection, test):
    """Test $zip with degenerate and edge case inputs."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
