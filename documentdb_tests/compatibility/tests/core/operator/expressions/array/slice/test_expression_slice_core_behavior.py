"""
Core behavior tests for $slice expression.

Tests 2-arg form (positive/negative n, n exceeds length, zero n, empty array),
3-arg form (position, negative position, n exceeds remaining, empty/single-element),
nested mixed arrays, large arrays, and literal array/index arguments.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX

# Property [Positive n]: a positive n returns the first n elements, capped at array length.
POSITIVE_N_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_1",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "n": 1},
        expected=[1],
        msg="$slice should return the first element",
    ),
    ExpressionTestCase(
        "first_2",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "n": 2},
        expected=[1, 2],
        msg="$slice should return the first 2 elements",
    ),
    ExpressionTestCase(
        "first_3",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "n": 3},
        expected=[1, 2, 3],
        msg="$slice should return the first 3 elements",
    ),
    ExpressionTestCase(
        "first_all",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": 3},
        expected=[1, 2, 3],
        msg="$slice should return all elements",
    ),
    ExpressionTestCase(
        "first_single",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [42], "n": 1},
        expected=[42],
        msg="$slice should return a single element",
    ),
    ExpressionTestCase(
        "first_strings",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": ["a", "b", "c"], "n": 2},
        expected=["a", "b"],
        msg="$slice should return the first 2 strings",
    ),
    ExpressionTestCase(
        "first_mixed",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, "two", True, None], "n": 3},
        expected=[1, "two", True],
        msg="$slice should return the first 3 mixed elements",
    ),
]

# Property [Negative n]: a negative n returns the last |n| elements, capped at array length.
NEGATIVE_N_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "last_1",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "n": -1},
        expected=[5],
        msg="$slice should return the last element",
    ),
    ExpressionTestCase(
        "last_2",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "n": -2},
        expected=[4, 5],
        msg="$slice should return the last 2 elements",
    ),
    ExpressionTestCase(
        "last_3",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "n": -3},
        expected=[3, 4, 5],
        msg="$slice should return the last 3 elements",
    ),
    ExpressionTestCase(
        "last_all",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": -3},
        expected=[1, 2, 3],
        msg="$slice should return all elements via negative n",
    ),
    ExpressionTestCase(
        "last_single",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [42], "n": -1},
        expected=[42],
        msg="$slice should return a single element via -1",
    ),
]

# Property [n Exceeds Length]: an n larger than the array returns the whole array.
N_EXCEEDS_LENGTH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pos_n_exceeds",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": 10},
        expected=[1, 2, 3],
        msg="$slice should return all when n exceeds length",
    ),
    ExpressionTestCase(
        "neg_n_exceeds",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": -10},
        expected=[1, 2, 3],
        msg="$slice should return all when negative n exceeds length",
    ),
    ExpressionTestCase(
        "pos_n_int32_max",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": INT32_MAX},
        expected=[1, 2, 3],
        msg="$slice should return all when n is INT32_MAX",
    ),
]

# Property [Zero n]: n of zero returns an empty array.
ZERO_N_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_n",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": 0},
        expected=[],
        msg="$slice should return empty for n=0",
    ),
    ExpressionTestCase(
        "zero_n_empty",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [], "n": 0},
        expected=[],
        msg="$slice should return empty for n=0 on an empty array",
    ),
]

# Property [Empty Array]: slicing an empty array returns an empty array.
EMPTY_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_pos_n",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [], "n": 5},
        expected=[],
        msg="$slice should return empty for positive n on an empty array",
    ),
    ExpressionTestCase(
        "empty_neg_n",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [], "n": -5},
        expected=[],
        msg="$slice should return empty for negative n on an empty array",
    ),
]

# Property [Position]: the 3-arg form starts slicing at the given position.
POSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pos_0_n_2",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": 0, "n": 2},
        expected=[1, 2],
        msg="$slice should slice from position 0",
    ),
    ExpressionTestCase(
        "pos_1_n_2",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": 1, "n": 2},
        expected=[2, 3],
        msg="$slice should slice from position 1",
    ),
    ExpressionTestCase(
        "pos_2_n_3",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": 2, "n": 3},
        expected=[3, 4, 5],
        msg="$slice should slice from position 2",
    ),
    ExpressionTestCase(
        "pos_0_n_all",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 0, "n": 3},
        expected=[1, 2, 3],
        msg="$slice should slice all from position 0",
    ),
    ExpressionTestCase(
        "pos_last_n_1",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 2, "n": 1},
        expected=[3],
        msg="$slice should slice the last element via position",
    ),
]

# Property [Negative Position]: a negative position counts from the end and clamps to the start.
NEGATIVE_POSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "neg_pos_1_n_1",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": -1, "n": 1},
        expected=[5],
        msg="$slice should slice from position -1",
    ),
    ExpressionTestCase(
        "neg_pos_2_n_2",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": -2, "n": 2},
        expected=[4, 5],
        msg="$slice should slice from position -2",
    ),
    ExpressionTestCase(
        "neg_pos_3_n_2",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": -3, "n": 2},
        expected=[3, 4],
        msg="$slice should slice from position -3",
    ),
    ExpressionTestCase(
        "neg_pos_exceeds_n_2",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": -10, "n": 2},
        expected=[1, 2],
        msg="$slice should clamp a negative position to the start",
    ),
    ExpressionTestCase(
        "neg_pos_all",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": -3, "n": 3},
        expected=[1, 2, 3],
        msg="$slice should slice all from a negative position",
    ),
]

# Property [Position n Exceeds]: n beyond the remaining elements returns what remains.
POSITION_N_EXCEEDS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pos_n_exceeds_remaining",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": 3, "n": 10},
        expected=[4, 5],
        msg="$slice should return the remaining elements when n exceeds",
    ),
    ExpressionTestCase(
        "pos_beyond_array",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 10, "n": 2},
        expected=[],
        msg="$slice should return empty when position is beyond the array",
    ),
    ExpressionTestCase(
        "pos_int32_max",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": INT32_MAX, "n": 2},
        expected=[],
        msg="$slice should return empty when position is INT32_MAX",
    ),
    ExpressionTestCase(
        "pos_eq_length",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": 5, "n": 3},
        expected=[],
        msg="$slice should return empty when position equals array length",
    ),
]

# Property [Empty Array With Position]: the 3-arg form on an empty array returns an empty array.
EMPTY_ARRAY_POSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_pos_0",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [], "pos": 0, "n": 3},
        expected=[],
        msg="$slice should return empty for an empty array with position 0",
    ),
    ExpressionTestCase(
        "empty_neg_pos",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [], "pos": -1, "n": 3},
        expected=[],
        msg="$slice should return empty for an empty array with a negative position",
    ),
    ExpressionTestCase(
        "empty_pos_beyond",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [], "pos": 5, "n": 3},
        expected=[],
        msg="$slice should return empty for an empty array with position beyond",
    ),
]

# Property [Single Element With Position]: position selects or misses the single element.
SINGLE_ELEMENT_POSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_pos_0_n_1",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": ["only"], "pos": 0, "n": 1},
        expected=["only"],
        msg="$slice should return the element at position 0",
    ),
    ExpressionTestCase(
        "single_neg_1_n_1",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": ["only"], "pos": -1, "n": 1},
        expected=["only"],
        msg="$slice should return the element via a negative position",
    ),
    ExpressionTestCase(
        "single_pos_past_end",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": ["only"], "pos": 1, "n": 1},
        expected=[],
        msg="$slice should return empty when position is past the single element",
    ),
]

# Property [Element Preservation]: sliced elements retain their type and value.
NESTED_MIXED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_bson_slice",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, "two", {"a": 1}, [3, 4], True, None, Decimal128("5.5")], "n": 4},
        expected=[1, "two", {"a": 1}, [3, 4]],
        msg="$slice should slice mixed BSON types",
    ),
    ExpressionTestCase(
        "mixed_bson_slice_neg",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, "two", {"a": 1}, [3, 4], True, None, Decimal128("5.5")], "n": -3},
        expected=[True, None, Decimal128("5.5")],
        msg="$slice should slice the last 3 mixed BSON types",
    ),
    ExpressionTestCase(
        "deeply_nested_slice",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [[[1, 2], [3, 4]], [[5, 6]], "end"], "n": 2},
        expected=[[[1, 2], [3, 4]], [[5, 6]]],
        msg="$slice should slice deeply nested arrays",
    ),
]

# Property [Large Array]: slicing works on large arrays.
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_first_5",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": list(range(10_000)), "n": 5},
        expected=[0, 1, 2, 3, 4],
        msg="$slice should slice the first 5 from a large array",
    ),
    ExpressionTestCase(
        "large_last_5",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": list(range(10_000)), "n": -5},
        expected=[9_995, 9_996, 9_997, 9_998, 9_999],
        msg="$slice should slice the last 5 from a large array",
    ),
    ExpressionTestCase(
        "large_pos_middle",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": list(range(10_000)), "pos": 5_000, "n": 3},
        expected=[5_000, 5_001, 5_002],
        msg="$slice should slice from the middle of a large array",
    ),
]

ALL_TESTS = (
    POSITIVE_N_TESTS
    + NEGATIVE_N_TESTS
    + N_EXCEEDS_LENGTH_TESTS
    + ZERO_N_TESTS
    + EMPTY_ARRAY_TESTS
    + POSITION_TESTS
    + NEGATIVE_POSITION_TESTS
    + POSITION_N_EXCEEDS_TESTS
    + EMPTY_ARRAY_POSITION_TESTS
    + SINGLE_ELEMENT_POSITION_TESTS
    + NESTED_MIXED_TESTS
    + LARGE_ARRAY_TESTS
)

# Property [Literal Arguments]: $slice accepts literal array and index arguments.
LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_first_1",
        expression={"$slice": [[1, 2, 3, 4, 5], 1]},
        expected=[1],
        msg="$slice should return the first element from literal arguments",
    ),
    ExpressionTestCase(
        "literal_last_1",
        expression={"$slice": [[1, 2, 3, 4, 5], -1]},
        expected=[5],
        msg="$slice should return the last element from literal arguments",
    ),
    ExpressionTestCase(
        "literal_pos_0_n_2",
        expression={"$slice": [[1, 2, 3, 4, 5], 0, 2]},
        expected=[1, 2],
        msg="$slice should slice from a literal position",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_slice_literal(collection, test):
    """Test $slice with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_slice_insert(collection, test):
    """Test $slice with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
