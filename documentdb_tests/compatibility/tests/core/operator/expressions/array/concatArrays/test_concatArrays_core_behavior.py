"""
Core behavior tests for $concatArrays expression.

Tests concatenation of arrays with various element types, empty arrays,
single arrays, multiple arrays, nested arrays, duplicates, null
propagation, and large arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Concatenation]: $concatArrays joins multiple arrays into one in argument order.
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "two_int_arrays",
        doc={"arr0": [1, 2], "arr1": [3, 4]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[1, 2, 3, 4],
        msg="$concatArrays should concatenate two int arrays",
    ),
    ExpressionTestCase(
        "two_string_arrays",
        doc={"arr0": ["a", "b"], "arr1": ["c", "d"]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=["a", "b", "c", "d"],
        msg="$concatArrays should concatenate two string arrays",
    ),
    ExpressionTestCase(
        "three_arrays",
        doc={"arr0": [1, 2], "arr1": [3, 4], "arr2": [5, 6]},
        expression={"$concatArrays": ["$arr0", "$arr1", "$arr2"]},
        expected=[1, 2, 3, 4, 5, 6],
        msg="$concatArrays should concatenate three arrays",
    ),
    ExpressionTestCase(
        "mixed_type_elements",
        doc={"arr0": [1, "two"], "arr1": [True, None, {"a": 1}]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[1, "two", True, None, {"a": 1}],
        msg="$concatArrays should concatenate arrays with mixed types",
    ),
]

# Property [Empty Arrays]: $concatArrays treats empty arrays as contributing no elements.
EMPTY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "both_empty",
        doc={"arr0": [], "arr1": []},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[],
        msg="$concatArrays should return empty array for two empty arrays",
    ),
    ExpressionTestCase(
        "first_empty",
        doc={"arr0": [], "arr1": [1, 2]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[1, 2],
        msg="$concatArrays should return second array when first is empty",
    ),
    ExpressionTestCase(
        "second_empty",
        doc={"arr0": [1, 2], "arr1": []},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[1, 2],
        msg="$concatArrays should return first array when second is empty",
    ),
    ExpressionTestCase(
        "all_empty",
        doc={"arr0": [], "arr1": [], "arr2": []},
        expression={"$concatArrays": ["$arr0", "$arr1", "$arr2"]},
        expected=[],
        msg="$concatArrays should return empty array for all empty inputs",
    ),
    ExpressionTestCase(
        "no_arguments",
        doc={"x": 1},
        expression={"$concatArrays": []},
        expected=[],
        msg="$concatArrays should return an empty array for no arguments",
    ),
    ExpressionTestCase(
        "empty_between_nonempty",
        doc={"arr0": [1], "arr1": [], "arr2": [2]},
        expression={"$concatArrays": ["$arr0", "$arr1", "$arr2"]},
        expected=[1, 2],
        msg="$concatArrays should skip an empty array between non-empty arrays",
    ),
    ExpressionTestCase(
        "multiple_empty",
        doc={"arr0": [], "arr1": [], "arr2": [], "arr3": []},
        expression={"$concatArrays": ["$arr0", "$arr1", "$arr2", "$arr3"]},
        expected=[],
        msg="$concatArrays should return an empty array for multiple empty arrays",
    ),
]

# Property [Single Array]: $concatArrays returns a single array argument unchanged.
SINGLE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_array",
        doc={"arr0": [1, 2, 3]},
        expression={"$concatArrays": ["$arr0"]},
        expected=[1, 2, 3],
        msg="$concatArrays should return the single array unchanged",
    ),
    ExpressionTestCase(
        "single_empty_array",
        doc={"arr0": []},
        expression={"$concatArrays": ["$arr0"]},
        expected=[],
        msg="$concatArrays should return empty array for single empty input",
    ),
]

# Property [Top Level Only]: $concatArrays joins at the top level without flattening.
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_subarrays",
        doc={"arr0": [[1, 2]], "arr1": [[3, 4]]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[[1, 2], [3, 4]],
        msg="$concatArrays should concatenate top-level, not flatten subarrays",
    ),
    ExpressionTestCase(
        "mixed_nested",
        doc={"arr0": [[1], "two"], "arr1": [[3, 4]]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[[1], "two", [3, 4]],
        msg="$concatArrays should concatenate mixed nested elements",
    ),
    ExpressionTestCase(
        "deeply_nested",
        doc={"arr0": [[[1]]], "arr1": [[[2]]]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[[[1]], [[2]]],
        msg="$concatArrays should preserve deeply nested array elements",
    ),
    ExpressionTestCase(
        "empty_nested",
        doc={"arr0": [[]], "arr1": [[]]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[[], []],
        msg="$concatArrays should preserve empty nested arrays as elements",
    ),
]

# Property [Duplicates]: $concatArrays keeps duplicate elements from the inputs.
DUPLICATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "duplicate_elements",
        doc={"arr0": [1, 2, 3], "arr1": [2, 3, 4]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[1, 2, 3, 2, 3, 4],
        msg="$concatArrays should preserve duplicate elements across arrays",
    ),
    ExpressionTestCase(
        "identical_arrays",
        doc={"arr0": [1, 2], "arr1": [1, 2]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[1, 2, 1, 2],
        msg="$concatArrays should concatenate identical arrays",
    ),
]

# Property [Null Propagation]: $concatArrays returns null when any argument is null or missing.
NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first_arg",
        doc={"arr0": None, "arr1": [1, 2]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=None,
        msg="$concatArrays should return null when first argument is null",
    ),
    ExpressionTestCase(
        "null_second_arg",
        doc={"arr0": [1, 2], "arr1": None},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=None,
        msg="$concatArrays should return null when second argument is null",
    ),
    ExpressionTestCase(
        "all_null",
        doc={"arr0": None, "arr1": None},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=None,
        msg="$concatArrays should return null when all arguments are null",
    ),
    ExpressionTestCase(
        "null_among_three",
        doc={"arr0": [1], "arr1": None, "arr2": [2]},
        expression={"$concatArrays": ["$arr0", "$arr1", "$arr2"]},
        expected=None,
        msg="$concatArrays should return null when any argument is null",
    ),
    ExpressionTestCase(
        "null_elements_in_arrays",
        doc={"arr0": [1, None], "arr1": [None, 2]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[1, None, None, 2],
        msg="$concatArrays should preserve null elements within arrays",
    ),
]

# Property [Object Elements]: $concatArrays concatenates arrays of documents intact.
OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arrays_of_objects",
        doc={"arr0": [{"a": 1}], "arr1": [{"b": 2}]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[{"a": 1}, {"b": 2}],
        msg="$concatArrays should concatenate arrays of objects",
    ),
    ExpressionTestCase(
        "objects_with_arrays",
        doc={"arr0": [{"items": [1, 2]}], "arr1": [{"items": [3, 4]}]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=[{"items": [1, 2]}, {"items": [3, 4]}],
        msg="$concatArrays should preserve inner arrays in objects",
    ),
]

# Property [Large Arrays]: $concatArrays concatenates large arrays.
_LARGE_A = list(range(500))
_LARGE_B = list(range(500, 1000))

# Property [Large Arrays]: $concatArrays concatenates large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_arrays",
        doc={"arr0": _LARGE_A, "arr1": _LARGE_B},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=list(range(1000)),
        msg="$concatArrays should concatenate large arrays",
    ),
    ExpressionTestCase(
        "two_5000_arrays",
        doc={"arr0": list(range(5_000)), "arr1": list(range(5_000, 10000))},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=list(range(10_000)),
        msg="$concatArrays should concatenate two large arrays into 10,000 elements",
    ),
    ExpressionTestCase(
        "one_large_one_small",
        doc={"arr0": list(range(10_000)), "arr1": [10_000]},
        expression={"$concatArrays": ["$arr0", "$arr1"]},
        expected=list(range(10_001)),
        msg="$concatArrays should concatenate a large array and a small array",
    ),
    ExpressionTestCase(
        "100_single_element_arrays",
        doc={f"arr{i}": [i] for i in range(100)},
        expression={"$concatArrays": [f"$arr{i}" for i in range(100)]},
        expected=list(range(100)),
        msg="$concatArrays should concatenate 100 single-element arrays",
    ),
]

# Property [Many Arrays]: $concatArrays concatenates many array arguments.
MANY_ARRAYS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "five_arrays",
        doc={"arr0": [1], "arr1": [2], "arr2": [3], "arr3": [4], "arr4": [5]},
        expression={"$concatArrays": ["$arr0", "$arr1", "$arr2", "$arr3", "$arr4"]},
        expected=[1, 2, 3, 4, 5],
        msg="$concatArrays should concatenate five arrays",
    ),
    ExpressionTestCase(
        "ten_empty_arrays",
        doc={f"arr{i}": [] for i in range(10)},
        expression={"$concatArrays": [f"$arr{i}" for i in range(10)]},
        expected=[],
        msg="$concatArrays should concatenate ten empty arrays",
    ),
    ExpressionTestCase(
        "fifty_arrays",
        doc={f"arr{i}": [i] for i in range(50)},
        expression={"$concatArrays": [f"$arr{i}" for i in range(50)]},
        expected=list(range(50)),
        msg="$concatArrays should concatenate 50 arrays",
    ),
]

ALL_TESTS = (
    BASIC_TESTS
    + EMPTY_TESTS
    + SINGLE_ARRAY_TESTS
    + NESTED_ARRAY_TESTS
    + DUPLICATE_TESTS
    + NULL_TESTS
    + OBJECT_TESTS
    + LARGE_ARRAY_TESTS
    + MANY_ARRAYS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_concatArrays_insert(collection, test):
    """Test $concatArrays with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "two_int_arrays",
        doc=None,
        expression={"$concatArrays": [{"$literal": [1, 2]}, {"$literal": [3, 4]}]},
        expected=[1, 2, 3, 4],
        msg="$concatArrays should concatenate two literal int arrays",
    ),
    ExpressionTestCase(
        "three_arrays",
        doc=None,
        expression={
            "$concatArrays": [{"$literal": [1, 2]}, {"$literal": [3, 4]}, {"$literal": [5, 6]}]
        },
        expected=[1, 2, 3, 4, 5, 6],
        msg="$concatArrays should concatenate three literal arrays",
    ),
    ExpressionTestCase(
        "both_empty",
        doc=None,
        expression={"$concatArrays": [{"$literal": []}, {"$literal": []}]},
        expected=[],
        msg="$concatArrays should return empty for two literal empty arrays",
    ),
    ExpressionTestCase(
        "single_array",
        doc=None,
        expression={"$concatArrays": [{"$literal": [1, 2, 3]}]},
        expected=[1, 2, 3],
        msg="$concatArrays should return single literal array unchanged",
    ),
    ExpressionTestCase(
        "nested_subarrays",
        doc=None,
        expression={"$concatArrays": [{"$literal": [[1, 2]]}, {"$literal": [[3, 4]]}]},
        expected=[[1, 2], [3, 4]],
        msg="$concatArrays should concatenate literal nested subarrays",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_concatArrays_literal(collection, test):
    """Test $concatArrays with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
