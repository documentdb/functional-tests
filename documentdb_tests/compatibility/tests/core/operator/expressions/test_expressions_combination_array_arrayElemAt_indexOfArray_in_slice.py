"""
Combination tests for array expression operators: $arrayElemAt, $indexOfArray, $in, $slice.

Tests that verify these operators work correctly when composed with each other
and with other operators like $concatArrays, $reverseArray, $filter, $map, $size, etc.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class CombinationTest(BaseTestCase):
    """Test case for combination expression tests."""

    expr: Any = None


# ---------------------------------------------------------------------------
# $arrayElemAt combinations
# ---------------------------------------------------------------------------
ARRAY_ELEM_AT_COMBINATION_TESTS: list[CombinationTest] = [
    CombinationTest(
        id="arrayElemAt_index_from_indexOfArray",
        expr={"$arrayElemAt": [[10, 20, 30], {"$indexOfArray": [[10, 20, 30], 30]}]},
        expected=30,
        msg="Should use $indexOfArray result as index",
    ),
    CombinationTest(
        id="arrayElemAt_last_element_via_size",
        expr={"$arrayElemAt": [[10, 20, 30], {"$subtract": [{"$size": [[10, 20, 30]]}, 1]}]},
        expected=30,
        msg="Should access last element via $size - 1",
    ),
    CombinationTest(
        id="arrayElemAt_elem_from_slice",
        expr={"$arrayElemAt": [{"$slice": [[10, 20, 30, 40], -2]}, 0]},
        expected=30,
        msg="Should access element from $slice result",
    ),
    CombinationTest(
        id="arrayElemAt_elem_from_slice_3arg",
        expr={"$arrayElemAt": [{"$slice": [[10, 20, 30, 40], 1, 2]}, 1]},
        expected=30,
        msg="Should access element from $slice 3-arg result",
    ),
    CombinationTest(
        id="arrayElemAt_elem_from_reverseArray",
        expr={"$arrayElemAt": [{"$reverseArray": [[10, 20, 30]]}, 0]},
        expected=30,
        msg="Should access element from $reverseArray result",
    ),
    CombinationTest(
        id="arrayElemAt_elem_from_concatArrays",
        expr={"$arrayElemAt": [{"$concatArrays": [[10, 20], [30, 40]]}, 2]},
        expected=30,
        msg="Should access element from $concatArrays result",
    ),
    CombinationTest(
        id="arrayElemAt_computed_index",
        expr={"$arrayElemAt": [[10, 20, 30], {"$subtract": [3, 1]}]},
        expected=30,
        msg="Should use computed index from $subtract",
    ),
]

# ---------------------------------------------------------------------------
# $in combinations
# ---------------------------------------------------------------------------
IN_COMBINATION_TESTS: list[CombinationTest] = [
    CombinationTest(
        id="in_value_from_add",
        expr={"$in": [{"$add": [1, 1]}, [1, 2, 3]]},
        expected=True,
        msg="Should find value computed by $add",
    ),
    CombinationTest(
        id="in_array_from_concatArrays",
        expr={"$in": [3, {"$concatArrays": [[1, 2], [3, 4]]}]},
        expected=True,
        msg="Should search in $concatArrays result",
    ),
    CombinationTest(
        id="in_value_from_arrayElemAt",
        expr={"$in": [{"$arrayElemAt": [[10, 20, 30], 1]}, [5, 20, 35]]},
        expected=True,
        msg="Should find value from $arrayElemAt",
    ),
    CombinationTest(
        id="in_array_from_filter",
        expr={
            "$in": [
                4,
                {
                    "$filter": {
                        "input": [1, 2, 3, 4, 5],
                        "as": "n",
                        "cond": {"$gte": ["$$n", 3]},
                    }
                },
            ]
        },
        expected=True,
        msg="Should search in $filter result",
    ),
    CombinationTest(
        id="in_array_from_map",
        expr={
            "$in": [
                20,
                {
                    "$map": {
                        "input": [1, 2, 3],
                        "as": "n",
                        "in": {"$multiply": ["$$n", 10]},
                    }
                },
            ]
        },
        expected=True,
        msg="Should search in $map result",
    ),
    CombinationTest(
        id="in_array_from_reverseArray",
        expr={"$in": [1, {"$reverseArray": [[1, 2, 3]]}]},
        expected=True,
        msg="Should search in $reverseArray result",
    ),
    CombinationTest(
        id="in_cond_with_inner_in",
        expr={"$in": [5, {"$cond": [{"$in": ["a", ["a", "b"]]}, [5, 6], [7, 8]]}]},
        expected=True,
        msg="Should search in $cond-selected array",
    ),
    CombinationTest(
        id="in_inside_cond",
        expr={"$cond": [{"$in": [2, [1, 2, 3]]}, "found", "not_found"]},
        expected="found",
        msg="Should use $in result in $cond",
    ),
    CombinationTest(
        id="in_value_from_indexOfArray",
        expr={"$in": [{"$indexOfArray": [[10, 20, 30], 20]}, [0, 1, 2]]},
        expected=True,
        msg="Should find $indexOfArray result in array",
    ),
    CombinationTest(
        id="in_nested_decimal128",
        expr={
            "$in": [
                {"$arrayElemAt": [[Decimal128("1.1"), Decimal128("2.2")], 1]},
                [Decimal128("2.2"), Decimal128("3.3")],
            ]
        },
        expected=True,
        msg="Should find Decimal128 from $arrayElemAt in array",
    ),
]

# ---------------------------------------------------------------------------
# $indexOfArray combinations
# ---------------------------------------------------------------------------
INDEX_OF_ARRAY_COMBINATION_TESTS: list[CombinationTest] = [
    CombinationTest(
        id="indexOfArray_result_as_arrayElemAt_index",
        expr={"$arrayElemAt": [[10, 20, 30], {"$indexOfArray": [[10, 20, 30], 20]}]},
        expected=20,
        msg="Should use $indexOfArray result as $arrayElemAt index",
    ),
    CombinationTest(
        id="indexOfArray_search_from_add",
        expr={"$indexOfArray": [[1, 2, 3], {"$add": [1, 1]}]},
        expected=1,
        msg="Should search for value computed by $add",
    ),
    CombinationTest(
        id="indexOfArray_array_from_concatArrays",
        expr={"$indexOfArray": [{"$concatArrays": [[1, 2], [3, 4]]}, 3]},
        expected=2,
        msg="Should search in $concatArrays result",
    ),
    CombinationTest(
        id="indexOfArray_array_from_filter",
        expr={
            "$indexOfArray": [
                {"$filter": {"input": [1, 2, 3, 4, 5], "cond": {"$gt": ["$$this", 2]}}},
                4,
            ]
        },
        expected=1,
        msg="Should search in $filter result",
    ),
    CombinationTest(
        id="indexOfArray_result_in_cond",
        expr={"$cond": [{"$gte": [{"$indexOfArray": [[1, 2, 3], 2]}, 0]}, "found", "not_found"]},
        expected="found",
        msg="Should use $indexOfArray result in $cond",
    ),
    CombinationTest(
        id="indexOfArray_start_from_subtract",
        expr={"$indexOfArray": [[1, 2, 1, 2], 1, {"$subtract": [3, 1]}]},
        expected=2,
        msg="Should use $subtract result as start index",
    ),
    CombinationTest(
        id="indexOfArray_via_arrayElemAt",
        expr={
            "$indexOfArray": [
                ["a", "b", "c", "d"],
                {
                    "$arrayElemAt": [
                        ["a", "b", "c", "d"],
                        {"$indexOfArray": [[10, 20, 30], 20]},
                    ]
                },
            ]
        },
        expected=1,
        msg="Should search for value from nested $arrayElemAt/$indexOfArray",
    ),
    CombinationTest(
        id="indexOfArray_subarray_mixed_bson",
        expr={
            "$indexOfArray": [
                [[MinKey(), MaxKey()], [1, 2], "x"],
                {
                    "$arrayElemAt": [
                        [[MinKey(), MaxKey()], [1, 2], "x"],
                        {"$indexOfArray": [[[MinKey(), MaxKey()], [1, 2], "x"], [1, 2]]},
                    ]
                },
            ]
        },
        expected=1,
        msg="Should find mixed BSON subarray via nested operators",
    ),
    CombinationTest(
        id="indexOfArray_triple_nested_decimal128",
        expr={
            "$indexOfArray": [
                [Decimal128("1.1"), Decimal128("2.2"), Decimal128("3.3")],
                {
                    "$arrayElemAt": [
                        [Decimal128("1.1"), Decimal128("2.2"), Decimal128("3.3")],
                        {
                            "$indexOfArray": [
                                [Decimal128("1.1"), Decimal128("2.2"), Decimal128("3.3")],
                                Decimal128("3.3"),
                            ]
                        },
                    ]
                },
            ]
        },
        expected=2,
        msg="Should resolve triple-nested Decimal128 operators",
    ),
]

# ---------------------------------------------------------------------------
# $slice combinations
# ---------------------------------------------------------------------------
SLICE_COMBINATION_TESTS: list[CombinationTest] = [
    CombinationTest(
        id="slice_array_from_concatArrays",
        expr={"$slice": [{"$concatArrays": [[1, 2], [3, 4, 5]]}, 3]},
        expected=[1, 2, 3],
        msg="Should slice $concatArrays result",
    ),
    CombinationTest(
        id="slice_n_from_subtract",
        expr={"$slice": [[1, 2, 3, 4, 5], {"$subtract": [5, 2]}]},
        expected=[1, 2, 3],
        msg="Should use $subtract result as n",
    ),
    CombinationTest(
        id="slice_array_from_filter",
        expr={
            "$slice": [
                {
                    "$filter": {
                        "input": [1, 2, 3, 4, 5],
                        "as": "n",
                        "cond": {"$gte": ["$$n", 3]},
                    }
                },
                2,
            ]
        },
        expected=[3, 4],
        msg="Should slice $filter result",
    ),
    CombinationTest(
        id="slice_position_from_indexOfArray",
        expr={
            "$slice": [
                [10, 20, 30, 40, 50],
                {"$indexOfArray": [[10, 20, 30, 40, 50], 30]},
                2,
            ]
        },
        expected=[30, 40],
        msg="Should use $indexOfArray result as position",
    ),
    CombinationTest(
        id="slice_array_from_map",
        expr={
            "$slice": [
                {
                    "$map": {
                        "input": [1, 2, 3],
                        "as": "n",
                        "in": {"$multiply": ["$$n", 10]},
                    }
                },
                2,
            ]
        },
        expected=[10, 20],
        msg="Should slice $map result",
    ),
    CombinationTest(
        id="slice_array_from_reverseArray",
        expr={"$slice": [{"$reverseArray": [[1, 2, 3, 4, 5]]}, 3]},
        expected=[5, 4, 3],
        msg="Should slice $reverseArray result",
    ),
    CombinationTest(
        id="slice_n_from_size",
        expr={"$slice": [[10, 20, 30, 40], {"$subtract": [{"$size": [[10, 20, 30, 40]]}, 1]}]},
        expected=[10, 20, 30],
        msg="Should use $size-based computation as n",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate all combination tests
# ---------------------------------------------------------------------------
ALL_COMBINATION_TESTS = (
    ARRAY_ELEM_AT_COMBINATION_TESTS
    + IN_COMBINATION_TESTS
    + INDEX_OF_ARRAY_COMBINATION_TESTS
    + SLICE_COMBINATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_COMBINATION_TESTS))
def test_combination_expression(collection, test):
    """Test array operators composed with other operators."""
    result = execute_expression(collection, test.expr)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Standalone tests for behavior that doesn't fit the dataclass pattern
# ---------------------------------------------------------------------------
def test_arrayElemAt_oob_is_missing_not_null(collection):
    """Test out-of-bounds result is truly MISSING (field absent), not null."""
    result = execute_expression(collection, {"$type": {"$arrayElemAt": [[1, 2, 3], 10]}})
    assert_expression_result(result, expected="missing")


def test_arrayElemAt_regex_type_preserved(collection):
    """Test $arrayElemAt preserves regex element type."""
    result = execute_expression(collection, {"$type": {"$arrayElemAt": [[Regex("abc")], 0]}})
    assert_expression_result(result, expected="regex")
