"""
Combination tests for array expression operators: $arrayElemAt, $indexOfArray, $in, $slice.

Tests that verify these operators work correctly when composed with each other
and with other operators like $concatArrays, $reverseArray, $filter, $map, $size, etc.
"""

import pytest
from bson import Decimal128, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_ELEM_AT_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="arrayElemAt_index_from_indexOfArray",
        expression={"$arrayElemAt": [[10, 20, 30], {"$indexOfArray": [[10, 20, 30], 30]}]},
        expected=30,
        msg="Should use $indexOfArray result as index",
    ),
    ExpressionTestCase(
        id="arrayElemAt_last_element_via_size",
        expression={"$arrayElemAt": [[10, 20, 30], {"$subtract": [{"$size": [[10, 20, 30]]}, 1]}]},
        expected=30,
        msg="Should access last element via $size - 1",
    ),
    ExpressionTestCase(
        id="arrayElemAt_elem_from_slice",
        expression={"$arrayElemAt": [{"$slice": [[10, 20, 30, 40], -2]}, 0]},
        expected=30,
        msg="Should access element from $slice result",
    ),
    ExpressionTestCase(
        id="arrayElemAt_elem_from_slice_3arg",
        expression={"$arrayElemAt": [{"$slice": [[10, 20, 30, 40], 1, 2]}, 1]},
        expected=30,
        msg="Should access element from $slice 3-arg result",
    ),
    ExpressionTestCase(
        id="arrayElemAt_elem_from_reverseArray",
        expression={"$arrayElemAt": [{"$reverseArray": [[10, 20, 30]]}, 0]},
        expected=30,
        msg="Should access element from $reverseArray result",
    ),
    ExpressionTestCase(
        id="arrayElemAt_elem_from_concatArrays",
        expression={"$arrayElemAt": [{"$concatArrays": [[10, 20], [30, 40]]}, 2]},
        expected=30,
        msg="Should access element from $concatArrays result",
    ),
    ExpressionTestCase(
        id="arrayElemAt_computed_index",
        expression={"$arrayElemAt": [[10, 20, 30], {"$subtract": [3, 1]}]},
        expected=30,
        msg="Should use computed index from $subtract",
    ),
]

# $in combinations
IN_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="in_value_from_add",
        expression={"$in": [{"$add": [1, 1]}, [1, 2, 3]]},
        expected=True,
        msg="Should find value computed by $add",
    ),
    ExpressionTestCase(
        id="in_array_from_concatArrays",
        expression={"$in": [3, {"$concatArrays": [[1, 2], [3, 4]]}]},
        expected=True,
        msg="Should search in $concatArrays result",
    ),
    ExpressionTestCase(
        id="in_value_from_arrayElemAt",
        expression={"$in": [{"$arrayElemAt": [[10, 20, 30], 1]}, [5, 20, 35]]},
        expected=True,
        msg="Should find value from $arrayElemAt",
    ),
    ExpressionTestCase(
        id="in_array_from_filter",
        expression={
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
    ExpressionTestCase(
        id="in_array_from_map",
        expression={
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
    ExpressionTestCase(
        id="in_array_from_reverseArray",
        expression={"$in": [1, {"$reverseArray": [[1, 2, 3]]}]},
        expected=True,
        msg="Should search in $reverseArray result",
    ),
    ExpressionTestCase(
        id="in_cond_with_inner_in",
        expression={"$in": [5, {"$cond": [{"$in": ["a", ["a", "b"]]}, [5, 6], [7, 8]]}]},
        expected=True,
        msg="Should search in $cond-selected array",
    ),
    ExpressionTestCase(
        id="in_inside_cond",
        expression={"$cond": [{"$in": [2, [1, 2, 3]]}, "found", "not_found"]},
        expected="found",
        msg="Should use $in result in $cond",
    ),
    ExpressionTestCase(
        id="in_value_from_indexOfArray",
        expression={"$in": [{"$indexOfArray": [[10, 20, 30], 20]}, [0, 1, 2]]},
        expected=True,
        msg="Should find $indexOfArray result in array",
    ),
    ExpressionTestCase(
        id="in_nested_decimal128",
        expression={
            "$in": [
                {"$arrayElemAt": [[Decimal128("1.1"), Decimal128("2.2")], 1]},
                [Decimal128("2.2"), Decimal128("3.3")],
            ]
        },
        expected=True,
        msg="Should find Decimal128 from $arrayElemAt in array",
    ),
]

# $indexOfArray combinations
INDEX_OF_ARRAY_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="indexOfArray_result_as_arrayElemAt_index",
        expression={"$arrayElemAt": [[10, 20, 30], {"$indexOfArray": [[10, 20, 30], 20]}]},
        expected=20,
        msg="Should use $indexOfArray result as $arrayElemAt index",
    ),
    ExpressionTestCase(
        id="indexOfArray_search_from_add",
        expression={"$indexOfArray": [[1, 2, 3], {"$add": [1, 1]}]},
        expected=1,
        msg="Should search for value computed by $add",
    ),
    ExpressionTestCase(
        id="indexOfArray_array_from_concatArrays",
        expression={"$indexOfArray": [{"$concatArrays": [[1, 2], [3, 4]]}, 3]},
        expected=2,
        msg="Should search in $concatArrays result",
    ),
    ExpressionTestCase(
        id="indexOfArray_array_from_filter",
        expression={
            "$indexOfArray": [
                {"$filter": {"input": [1, 2, 3, 4, 5], "cond": {"$gt": ["$$this", 2]}}},
                4,
            ]
        },
        expected=1,
        msg="Should search in $filter result",
    ),
    ExpressionTestCase(
        id="indexOfArray_result_in_cond",
        expression={
            "$cond": [{"$gte": [{"$indexOfArray": [[1, 2, 3], 2]}, 0]}, "found", "not_found"]
        },
        expected="found",
        msg="Should use $indexOfArray result in $cond",
    ),
    ExpressionTestCase(
        id="indexOfArray_start_from_subtract",
        expression={"$indexOfArray": [[1, 2, 1, 2], 1, {"$subtract": [3, 1]}]},
        expected=2,
        msg="Should use $subtract result as start index",
    ),
    ExpressionTestCase(
        id="indexOfArray_via_arrayElemAt",
        expression={
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
    ExpressionTestCase(
        id="indexOfArray_subarray_mixed_bson",
        expression={
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
    ExpressionTestCase(
        id="indexOfArray_triple_nested_decimal128",
        expression={
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

# $slice combinations
SLICE_COMBINATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="slice_array_from_concatArrays",
        expression={"$slice": [{"$concatArrays": [[1, 2], [3, 4, 5]]}, 3]},
        expected=[1, 2, 3],
        msg="Should slice $concatArrays result",
    ),
    ExpressionTestCase(
        id="slice_n_from_subtract",
        expression={"$slice": [[1, 2, 3, 4, 5], {"$subtract": [5, 2]}]},
        expected=[1, 2, 3],
        msg="Should use $subtract result as n",
    ),
    ExpressionTestCase(
        id="slice_array_from_filter",
        expression={
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
    ExpressionTestCase(
        id="slice_position_from_indexOfArray",
        expression={
            "$slice": [
                [10, 20, 30, 40, 50],
                {"$indexOfArray": [[10, 20, 30, 40, 50], 30]},
                2,
            ]
        },
        expected=[30, 40],
        msg="Should use $indexOfArray result as position",
    ),
    ExpressionTestCase(
        id="slice_array_from_map",
        expression={
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
    ExpressionTestCase(
        id="slice_array_from_reverseArray",
        expression={"$slice": [{"$reverseArray": [[1, 2, 3, 4, 5]]}, 3]},
        expected=[5, 4, 3],
        msg="Should slice $reverseArray result",
    ),
    ExpressionTestCase(
        id="slice_n_from_size",
        expression={
            "$slice": [[10, 20, 30, 40], {"$subtract": [{"$size": [[10, 20, 30, 40]]}, 1]}]
        },
        expected=[10, 20, 30],
        msg="Should use $size-based computation as n",
    ),
]

# Aggregate all combination tests
ALL_COMBINATION_TESTS = (
    ARRAY_ELEM_AT_COMBINATION_TESTS
    + IN_COMBINATION_TESTS
    + INDEX_OF_ARRAY_COMBINATION_TESTS
    + SLICE_COMBINATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_COMBINATION_TESTS))
def test_combination_expression(collection, test):
    """Test array operators composed with other operators."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Standalone tests for behavior that doesn't fit the dataclass pattern
def test_arrayElemAt_oob_is_missing_not_null(collection):
    """Test out-of-bounds result is truly MISSING (field absent), not null."""
    result = execute_expression(collection, {"$type": {"$arrayElemAt": [[1, 2, 3], 10]}})
    assert_expression_result(result, expected="missing")


def test_arrayElemAt_regex_type_preserved(collection):
    """Test $arrayElemAt preserves regex element type."""
    result = execute_expression(collection, {"$type": {"$arrayElemAt": [[Regex("abc")], 0]}})
    assert_expression_result(result, expected="regex")
