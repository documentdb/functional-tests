"""Tests for $setDifference core behavior: difference, dedup, ordering, asymmetry, and nesting."""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, MaxKey, MinKey, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_ZERO,
)

# Property [Basic Difference]: the result holds the deduplicated elements of the
# first array that are absent from the second.
SETDIFFERENCE_BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "basic_difference",
        doc={"arr1": ["a", "c"], "arr2": ["a", "b"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["c"],
        msg="Should return elements in first not in second",
    ),
    ExpressionTestCase(
        "complete_overlap",
        doc={"arr1": ["a", "c"], "arr2": ["a", "b", "c"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when second is superset",
    ),
    ExpressionTestCase(
        "no_overlap",
        doc={"arr1": ["a", "b"], "arr2": ["c", "d"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a", "b"],
        msg="Should return all when no overlap",
    ),
    ExpressionTestCase(
        "identical_arrays",
        doc={"arr1": ["a", "b"], "arr2": ["a", "b"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty for identical arrays",
    ),
    ExpressionTestCase(
        "first_empty",
        doc={"arr1": [], "arr2": ["a", "b"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when first is empty",
    ),
    ExpressionTestCase(
        "second_empty",
        doc={"arr1": ["a", "b"], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a", "b"],
        msg="Should return all when second is empty",
    ),
    ExpressionTestCase(
        "both_empty",
        doc={"arr1": [], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when both empty",
    ),
    ExpressionTestCase(
        "single_present",
        doc={"arr1": ["a"], "arr2": ["a"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Single element present in second returns empty",
    ),
    ExpressionTestCase(
        "single_absent",
        doc={"arr1": ["a"], "arr2": ["b"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a"],
        msg="Single element absent from second returns it",
    ),
    ExpressionTestCase(
        "result_always_array_single",
        doc={"arr1": ["a", "b"], "arr2": ["b"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a"],
        msg="Single element result should be array",
    ),
    ExpressionTestCase(
        "int_basic",
        doc={"arr1": [1, 2, 3, 4], "arr2": [1, 2, 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[4],
        msg="Should compute difference with ints",
    ),
    ExpressionTestCase(
        "int_no_overlap",
        doc={"arr1": [1, 2, 3, 4], "arr2": [1, 2, 3, 5, 6]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[4],
        msg="Should return only elements unique to first with partial integer overlap",
    ),
    ExpressionTestCase(
        "int_subset",
        doc={"arr1": [2, 3], "arr2": [2, 3, 4]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when first is subset of second",
    ),
    ExpressionTestCase(
        "string_diff",
        doc={"arr1": ["y", "z", "j"], "arr2": ["x", "y", "z"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["j"],
        msg="Should compute difference with strings",
    ),
    ExpressionTestCase(
        "int_vs_string_no_overlap",
        doc={"arr1": [1, 2, 3], "arr2": ["x", "y", "z"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, 2, 3],
        msg="Should return all elements when integer and string types have no overlap",
    ),
]

# Property [Duplicate Handling]: set semantics deduplicate both arrays before
# computing the difference.
SETDIFFERENCE_DUPES_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dupes_in_first",
        doc={"arr1": ["a", "a", "b"], "arr2": ["b"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a"],
        msg="Should deduplicate first array",
    ),
    ExpressionTestCase(
        "dupes_in_second",
        doc={"arr1": ["a", "b"], "arr2": ["b", "b", "b"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a"],
        msg="Should handle duplicates in second array without affecting result",
    ),
    ExpressionTestCase(
        "dupes_in_both",
        doc={"arr1": ["a", "a", "b", "b"], "arr2": ["b", "b"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a"],
        msg="Should deduplicate both",
    ),
    ExpressionTestCase(
        "all_duped_removed",
        doc={"arr1": ["a", "a"], "arr2": ["a"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when all removed",
    ),
    ExpressionTestCase(
        "all_same_not_in_second",
        doc={"arr1": ["a", "a", "a"], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a"],
        msg="Should deduplicate to single element",
    ),
    ExpressionTestCase(
        "heavy_dupes_first",
        doc={"arr1": [1, 2, 3, 2, 2, 3, 3, 3], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, 2, 3],
        msg="Should deduplicate heavy duplicates",
    ),
    ExpressionTestCase(
        "heavy_dupes_both",
        doc={"arr1": [1, 2, 3, 3, 2, 3, 2, 3], "arr2": [1, 2, 3, 2, 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Heavy duplicates in both returns empty",
    ),
    ExpressionTestCase(
        "int_dupes_second",
        doc={"arr1": [1, 2, 3], "arr2": [1, 1, 2, 2, 3, 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when all elements match despite duplicates in second",
    ),
    ExpressionTestCase(
        "order_independent",
        doc={"arr1": ["c", "a", "b"], "arr2": ["b", "a"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["c"],
        msg="Order should not matter for matching",
    ),
]

# Property [Asymmetry]: A minus B is not the same as B minus A.
SETDIFFERENCE_ASYMMETRY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "asym_partial_overlap_ab",
        doc={"arr1": [1, 2, 3], "arr2": [2, 3, 4]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should return only first-unique elements for partial overlap forward",
    ),
    ExpressionTestCase(
        "asym_partial_overlap_ba",
        doc={"arr1": [2, 3, 4], "arr2": [1, 2, 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[4],
        msg="Should return only first-unique elements for partial overlap reversed",
    ),
    ExpressionTestCase(
        "asym_identical",
        doc={"arr1": [1, 2], "arr2": [1, 2]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty for identical arrays",
    ),
    ExpressionTestCase(
        "asym_first_nonempty_ab",
        doc={"arr1": [1], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1],
        msg="Should return all elements when subtracting empty array",
    ),
    ExpressionTestCase(
        "asym_first_nonempty_ba",
        doc={"arr1": [], "arr2": [1]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when first array is empty",
    ),
    ExpressionTestCase(
        "asym_multi_elem_ab",
        doc={"arr1": [1, 2], "arr2": [3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, 2],
        msg="Should return all first elements when second has no overlap",
    ),
    ExpressionTestCase(
        "asym_multi_elem_ba",
        doc={"arr1": [3], "arr2": [1, 2]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[3],
        msg="Should return first element when it has no overlap with second",
    ),
    ExpressionTestCase(
        "asym_no_overlap_forward",
        doc={"arr1": [1, 2, 3], "arr2": [4, 5, 6]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, 2, 3],
        msg="Should return all first elements when no overlap forward",
    ),
    ExpressionTestCase(
        "asym_no_overlap_reverse",
        doc={"arr1": [4, 5, 6], "arr2": [1, 2, 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[4, 5, 6],
        msg="Should return all first elements when no overlap reversed",
    ),
    ExpressionTestCase(
        "asym_empty_first_forward",
        doc={"arr1": [], "arr2": [1, 2, 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when first is empty and second has elements",
    ),
    ExpressionTestCase(
        "asym_empty_second_reverse",
        doc={"arr1": [4, 5, 6], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[4, 5, 6],
        msg="Should return all elements when second is empty reversed",
    ),
]

# Property [Result Ordering]: the result preserves the first array's insertion order.
SETDIFFERENCE_ORDER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_order",
        doc={"arr1": ["red", "blue", "green"], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["red", "blue", "green"],
        msg="Should preserve insertion order for string elements",
    ),
    ExpressionTestCase(
        "int_order",
        doc={"arr1": [INT32_MAX, 0, INT32_MIN], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[INT32_MAX, 0, INT32_MIN],
        msg="Should preserve insertion order for integer elements",
    ),
    ExpressionTestCase(
        "long_order",
        doc={"arr1": [Int64(INT32_MAX), INT64_ZERO, Int64(INT32_MIN)], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Int64(INT32_MAX), INT64_ZERO, Int64(INT32_MIN)],
        msg="Should preserve insertion order for long elements",
    ),
    ExpressionTestCase(
        "decimal_order",
        doc={
            "arr1": [DECIMAL128_TWO_AND_HALF, DECIMAL128_ZERO, DECIMAL128_NEGATIVE_ONE_AND_HALF],
            "arr2": [],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[DECIMAL128_TWO_AND_HALF, DECIMAL128_ZERO, DECIMAL128_NEGATIVE_ONE_AND_HALF],
        msg="Should preserve insertion order for decimal128 elements",
    ),
    ExpressionTestCase(
        "bool_order",
        doc={"arr1": [True, False], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[True, False],
        msg="Should preserve insertion order for boolean elements",
    ),
    ExpressionTestCase(
        "date_order",
        doc={
            "arr1": [
                datetime(2023, 1, 1, tzinfo=timezone.utc),
                datetime(2018, 1, 1, tzinfo=timezone.utc),
                datetime(2017, 1, 1, tzinfo=timezone.utc),
            ],
            "arr2": [],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[
            datetime(2023, 1, 1, tzinfo=timezone.utc),
            datetime(2018, 1, 1, tzinfo=timezone.utc),
            datetime(2017, 1, 1, tzinfo=timezone.utc),
        ],
        msg="Should preserve insertion order for date elements",
    ),
    ExpressionTestCase(
        "timestamp_order",
        doc={"arr1": [Timestamp(1981, 0), Timestamp(1980, 0)], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[Timestamp(1981, 0), Timestamp(1980, 0)],
        msg="Should preserve insertion order for timestamp elements",
    ),
    ExpressionTestCase(
        "special_bson_order",
        doc={"arr1": [FLOAT_INFINITY, MaxKey(), MinKey(), FLOAT_NEGATIVE_INFINITY], "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[FLOAT_INFINITY, MaxKey(), MinKey(), FLOAT_NEGATIVE_INFINITY],
        msg="Should preserve insertion order for special BSON values",
    ),
]

# Property [Atomic Nesting]: nested arrays are compared as whole elements, not
# descended into.
SETDIFFERENCE_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_atomic",
        doc={"arr1": ["a", "b"], "arr2": [["a", "b"]]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a", "b"],
        msg="Should treat nested array as atomic element distinct from its contents",
    ),
    ExpressionTestCase(
        "nested_match",
        doc={"arr1": [["a", "b"], "c"], "arr2": [["a", "b"]]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["c"],
        msg="Should remove matching nested arrays from result",
    ),
    ExpressionTestCase(
        "nested_different",
        doc={"arr1": [["a"], ["b"]], "arr2": [["a"]]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[["b"]],
        msg="Should preserve non-matching nested arrays",
    ),
    ExpressionTestCase(
        "deeply_nested",
        doc={"arr1": [[[1]], [[2]]], "arr2": [[[1]]]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[[[2]]],
        msg="Should handle deeply nested arrays as atomic elements",
    ),
    ExpressionTestCase(
        "nested_with_scalar",
        doc={"arr1": [[1, 2], 3], "arr2": [1, 2, 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[[1, 2]],
        msg="Should not descend into nested arrays when comparing with scalars",
    ),
    ExpressionTestCase(
        "nested_identical",
        doc={"arr1": [[1, 2], 3], "arr2": [[1, 2], 3]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty for identical arrays containing nested arrays",
    ),
    ExpressionTestCase(
        "empty_nested",
        doc={"arr1": [[]], "arr2": ["red"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[[]],
        msg="Should treat empty nested array as a distinct element from strings",
    ),
    ExpressionTestCase(
        "multi_level_remove_scalars",
        doc={"arr1": ["a", "b", ["a"], [["b"]], [[["c"]]]], "arr2": ["b", "a"]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[["a"], [["b"]], [[["c"]]]],
        msg="Should preserve nested arrays when removing only scalar elements",
    ),
    ExpressionTestCase(
        "multi_level_remove_nested",
        doc={"arr1": ["a", "b", ["a"], [["b"]], [[["c"]]]], "arr2": ["b", ["a"]]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a", [["b"]], [[["c"]]]],
        msg="Should remove single-nested array while preserving deeper nested arrays",
    ),
    ExpressionTestCase(
        "multi_level_remove_double_nested",
        doc={"arr1": ["a", "b", ["a"], [["b"]], [[["c"]]]], "arr2": [[["b"]], ["a"]]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a", "b", [[["c"]]]],
        msg="Should remove double-nested arrays while preserving scalars and triple-nested",
    ),
    ExpressionTestCase(
        "multi_level_remove_all_nested",
        doc={"arr1": ["a", "b", ["a"], [["b"]], [[["c"]]]], "arr2": [[[["c"]]], [["b"]], ["a"]]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a", "b"],
        msg="Should preserve only scalars when all nested arrays are removed",
    ),
    ExpressionTestCase(
        "multi_level_no_match",
        doc={"arr1": ["a", "b", ["a"], [["b"]], [[["c"]]]], "arr2": [[[["b"]]], [["a"]], ["c"]]},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a", "b", ["a"], [["b"]], [[["c"]]]],
        msg="Should return all elements when nesting depths differ between arrays",
    ),
    ExpressionTestCase(
        "nested_num_remove_scalars",
        doc={
            "arr1": [1, 2, [2], [[Int64(3)]], [[[Decimal128("4")]]]],
            "arr2": [1, Decimal128("2")],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[[2], [[Int64(3)]], [[[Decimal128("4")]]]],
        msg="Should apply numeric equivalence only at top level for nested arrays",
    ),
    ExpressionTestCase(
        "nested_num_equiv_in_nested",
        doc={
            "arr1": [1, 2, [2], [[Int64(3)]], [[[Decimal128("4e0")]]]],
            "arr2": [Int64(2), [Decimal128("200E-2")]],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, [[Int64(3)]], [[[Decimal128("4e0")]]]],
        msg="Should handle numeric equivalence within nested array elements",
    ),
    ExpressionTestCase(
        "nested_num_no_match_different_nesting",
        doc={
            "arr1": [1, Decimal128("2"), [2], [[Int64(3)]], [[[Decimal128("4e0")]]]],
            "arr2": [[[[4]], [[3]], [2]]],
        },
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[1, Decimal128("2"), [2], [[Int64(3)]], [[[Decimal128("4e0")]]]],
        msg="Should return all elements when nesting structure differs for numeric values",
    ),
]

# Property [Large Arrays]: the operator scales to large inputs and still
# deduplicates and computes the difference correctly.
SETDIFFERENCE_LARGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_identical",
        doc={"arr1": list(range(1000)), "arr2": list(range(1000))},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty for two identical 1000-element arrays",
    ),
    ExpressionTestCase(
        "large_first_small_second",
        doc={"arr1": list(range(1000)), "arr2": list(range(10))},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=list(range(10, 1000)),
        msg="Should return 990 elements when subtracting 10 from 1000-element array",
    ),
    ExpressionTestCase(
        "small_first_large_second",
        doc={"arr1": list(range(10)), "arr2": list(range(1000))},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=[],
        msg="Should return empty when 10-element array is subset of 1000-element array",
    ),
    ExpressionTestCase(
        "large_duplicates",
        doc={"arr1": ["a"] * 10_000, "arr2": []},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=["a"],
        msg="Should deduplicate 10000 identical elements to a single element",
    ),
    ExpressionTestCase(
        "scale_10k",
        doc={"arr1": list(range(10_000)), "arr2": list(range(5_000, 15_000))},
        expression={"$setDifference": ["$arr1", "$arr2"]},
        expected=list(range(5_000)),
        msg="Should return 5000 elements for 10K arrays with partial overlap",
    ),
]

SETDIFFERENCE_CORE_TESTS: list[ExpressionTestCase] = (
    SETDIFFERENCE_BASIC_TESTS
    + SETDIFFERENCE_DUPES_TESTS
    + SETDIFFERENCE_ASYMMETRY_TESTS
    + SETDIFFERENCE_ORDER_TESTS
    + SETDIFFERENCE_NESTED_TESTS
    + SETDIFFERENCE_LARGE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETDIFFERENCE_CORE_TESTS))
def test_setDifference_core(collection, test):
    """Test $setDifference core behavior with field-reference array operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
