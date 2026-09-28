"""Tests for $setIntersection core behavior: dedup, ordering, nesting, arity, and large arrays."""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Basic Intersection]: the result holds the deduplicated elements
# common to every operand array.
SETINTERSECTION_BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "partial_overlap",
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[2, 3],
        msg="$setIntersection should return common elements for partial overlap",
    ),
    ExpressionTestCase(
        "no_overlap",
        doc={"a": [1, 2, 3], "b": [4, 5, 6]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for disjoint arrays",
    ),
    ExpressionTestCase(
        "identical",
        doc={"a": ["a", "b"], "b": ["a", "b"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["a", "b"],
        msg="$setIntersection should return all elements for identical arrays",
    ),
    ExpressionTestCase(
        "second_subset_of_first",
        doc={"a": [1, 2, 3], "b": [2, 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[2, 3],
        msg="$setIntersection should return subset elements when second is subset of first",
    ),
    ExpressionTestCase(
        "first_subset_of_second",
        doc={"a": [2, 3], "b": [2, 3, 4]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[2, 3],
        msg="$setIntersection should return first elements when first is subset of second",
    ),
    ExpressionTestCase(
        "superset_second",
        doc={"a": ["red", "blue"], "b": ["red", "blue", "green"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["red", "blue"],
        msg="$setIntersection should return common elements when second is superset",
    ),
    ExpressionTestCase(
        "superset_first",
        doc={"a": ["red", "blue", "green"], "b": ["blue", "red"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["blue", "red"],
        msg="$setIntersection should return common elements when first is superset",
    ),
    ExpressionTestCase(
        "partial_overlap_strings",
        doc={"a": ["red", "blue"], "b": ["green", "red"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["red"],
        msg="$setIntersection should return single common string element",
    ),
    ExpressionTestCase(
        "single_match",
        doc={"a": [1], "b": [1]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1],
        msg="$setIntersection should return single element for matching single-element arrays",
    ),
    ExpressionTestCase(
        "single_no_match",
        doc={"a": [1], "b": [2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for non-matching single-element arrays",
    ),
    ExpressionTestCase(
        "int_vs_string_no_overlap",
        doc={"a": [1, 2, 3], "b": ["x", "y", "z"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for different types with no overlap",
    ),
    ExpressionTestCase(
        "mixed_types_partial",
        doc={"a": [1, "a", True, None], "b": [1, "b", True, None]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1, True, None],
        msg="$setIntersection should return matching elements across mixed types",
    ),
]

# Property [Empty Operands]: an empty operand yields an empty intersection
# because nothing is common to every array.
SETINTERSECTION_EMPTY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "both_empty",
        doc={"a": [], "b": []},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for two empty arrays",
    ),
    ExpressionTestCase(
        "first_empty",
        doc={"a": [], "b": ["a", "b"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when first is empty",
    ),
    ExpressionTestCase(
        "second_empty",
        doc={"a": ["a", "b"], "b": []},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when second is empty",
    ),
    ExpressionTestCase(
        "first_empty_ints",
        doc={"a": [], "b": [1, 2, 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when first is an empty int array",
    ),
    ExpressionTestCase(
        "second_empty_strings",
        doc={"a": ["red", "blue"], "b": []},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when second is an empty string array",
    ),
    ExpressionTestCase(
        "three_all_empty",
        doc={"a": [], "b": [], "c": []},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[],
        msg="$setIntersection should return empty for three empty arrays",
    ),
    ExpressionTestCase(
        "one_of_three_empty",
        doc={"a": ["a"], "b": [], "c": ["a"]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[],
        msg="$setIntersection should return empty when one of three arrays is empty",
    ),
]

# Property [Duplicate Handling]: set semantics deduplicate every operand before
# computing the intersection.
SETINTERSECTION_DUPES_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dupes_in_first",
        doc={"a": ["a", "a", "b"], "b": ["a", "b", "b"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["a", "b"],
        msg="$setIntersection should deduplicate both arrays",
    ),
    ExpressionTestCase(
        "dupes_in_second",
        doc={"a": ["a", "b"], "b": ["a", "a", "c"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["a"],
        msg="$setIntersection should return common elements ignoring duplicates in second",
    ),
    ExpressionTestCase(
        "dupes_in_both",
        doc={"a": ["a", "a"], "b": ["a", "a"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["a"],
        msg="$setIntersection should deduplicate to a single element",
    ),
    ExpressionTestCase(
        "multiple_dupes",
        doc={"a": ["a", "a", "b", "b"], "b": ["b", "b", "c", "c"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["b"],
        msg="$setIntersection should return the single common element deduplicated",
    ),
    ExpressionTestCase(
        "heavy_dupes_first",
        doc={"a": ["red", "red", "red"], "b": ["red"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["red"],
        msg="$setIntersection should return single element for heavy duplicates in first",
    ),
    ExpressionTestCase(
        "heavy_dupes_second",
        doc={"a": ["red"], "b": ["red", "red", "red", "red"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["red"],
        msg="$setIntersection should return single element for heavy duplicates in second",
    ),
    ExpressionTestCase(
        "single_array_with_dupes_strings",
        doc={"a": ["red", "red", "red", "blue", "blue"]},
        expression={"$setIntersection": ["$a"]},
        expected=["blue", "red"],
        msg="$setIntersection should deduplicate a single string array with duplicates",
    ),
    ExpressionTestCase(
        "numeric_dupes",
        doc={"a": [1, 2, 2, 2, 2], "b": [1, 1, 2, 2, 2, 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1, 2],
        msg="$setIntersection should deduplicate numeric arrays with duplicates",
    ),
    ExpressionTestCase(
        "no_overlap_with_dupes",
        doc={"a": [1, 2, 2, 2, 2], "b": [3, 4, 3, 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for no overlap even with duplicates",
    ),
    ExpressionTestCase(
        "dupes_three_arrays",
        doc={
            "a": ["red", "blue", "blue"],
            "b": ["red", "red", "red", "blue", "blue"],
            "c": ["red", "blue", "red", "blue"],
        },
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=["blue", "red"],
        msg="$setIntersection should deduplicate across three arrays",
    ),
    ExpressionTestCase(
        "dupes_four_arrays_single_common",
        doc={
            "a": ["red", "red", "blue", "blue"],
            "b": ["red", "blue", "blue", "blue"],
            "c": ["red", "blue"],
            "d": ["blue"],
        },
        expression={"$setIntersection": ["$a", "$b", "$c", "$d"]},
        expected=["blue"],
        msg="$setIntersection should return single common element for four arrays with duplicates",
    ),
]

# Property [Order Independence]: the result set does not depend on the order of
# elements within an operand or the order of the operands themselves.
SETINTERSECTION_ORDER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "elements_reordered",
        doc={"a": ["a", "b", "c"], "b": ["c", "b", "a"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["a", "b", "c"],
        msg="$setIntersection should return same result regardless of element order",
    ),
    ExpressionTestCase(
        "dupes_different_order",
        doc={"a": ["red", "blue"], "b": ["blue", "red", "blue"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["blue", "red"],
        msg="$setIntersection should return same result regardless of order and duplicates",
    ),
    ExpressionTestCase(
        "args_abc",
        doc={"a": [1, 2, 3], "b": [2, 3, 4], "c": [3, 4, 5]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[3],
        msg="$setIntersection should return same result for a, b, c argument order",
    ),
    ExpressionTestCase(
        "args_bac",
        doc={"a": [2, 3, 4], "b": [1, 2, 3], "c": [3, 4, 5]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[3],
        msg="$setIntersection should return same result for b, a, c argument order",
    ),
    ExpressionTestCase(
        "args_cba",
        doc={"a": [3, 4, 5], "b": [2, 3, 4], "c": [1, 2, 3]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[3],
        msg="$setIntersection should return same result for c, b, a argument order",
    ),
]

# Property [Atomic Nesting]: array elements are compared as whole values and are
# not descended into.
SETINTERSECTION_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_vs_array",
        doc={"a": ["a", "b"], "b": [["a", "b"]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when a string differs from an array element",
    ),
    ExpressionTestCase(
        "nested_vs_scalar",
        doc={"a": ["red", "blue"], "b": [["red"], ["blue"]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty without descending into nested arrays",
    ),
    ExpressionTestCase(
        "nested_vs_scalar_wrapping",
        doc={"a": ["red", "blue"], "b": [["red", "blue"]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when a string differs from a nested array",
    ),
    ExpressionTestCase(
        "matching_nested",
        doc={"a": [[1, 2], [3, 4]], "b": [[1, 2], [5, 6]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[[1, 2]],
        msg="$setIntersection should match nested arrays at the top level",
    ),
    ExpressionTestCase(
        "nested_order_matters",
        doc={"a": [[1, 2]], "b": [[2, 1]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when nested array element order differs",
    ),
    ExpressionTestCase(
        "deeply_nested",
        doc={"a": [[[1]]], "b": [[[1]]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[[[1]]],
        msg="$setIntersection should match deeply nested arrays",
    ),
    ExpressionTestCase(
        "mixed_nesting",
        doc={"a": [1, [1]], "b": [1, [1]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[1, [1]],
        msg="$setIntersection should match both scalar and nested elements",
    ),
    ExpressionTestCase(
        "mixed_nesting_partial",
        doc={"a": [1, [1]], "b": [[1], 2]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[[1]],
        msg="$setIntersection should match only the nested array element",
    ),
    ExpressionTestCase(
        "deeply_nested_strings",
        doc={"a": [["red", "blue"]], "b": [["red", "blue"]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[["red", "blue"]],
        msg="$setIntersection should match nested string arrays",
    ),
    ExpressionTestCase(
        "deeply_nested_diff_order",
        doc={"a": [["red", "blue"]], "b": [["blue", "red"]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when nested string array order differs",
    ),
    ExpressionTestCase(
        "nested_three_arrays_match",
        doc={"a": [[1, 2]], "b": [[1, 2]], "c": [[1, 2]]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[[1, 2]],
        msg="$setIntersection should return the nested match across three arrays",
    ),
    ExpressionTestCase(
        "nested_three_arrays_no_match",
        doc={"a": [["red", "blue"]], "b": [["red", "blue"]], "c": [["blue", "red"]]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[],
        msg="$setIntersection should return empty when the third array breaks the nested match",
    ),
    ExpressionTestCase(
        "different_nesting_levels",
        doc={"a": [["red", "blue"]], "b": [[["red", "blue"]]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty for different nesting levels",
    ),
    ExpressionTestCase(
        "nested_array_vs_scalars",
        doc={"a": [[1, 2]], "b": [1, 2, 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when a nested array differs from scalar elements",
    ),
    ExpressionTestCase(
        "scalar_vs_nested_element",
        doc={"a": [1, 2], "b": [[1, 2], 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[],
        msg="$setIntersection should return empty when scalars differ from a nested array element",
    ),
    ExpressionTestCase(
        "nested_match_among_mixed",
        doc={"a": [[1, 2]], "b": [[1, 2], 3]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[[1, 2]],
        msg="$setIntersection should return the matching nested array among mixed elements",
    ),
    ExpressionTestCase(
        "nested_numeric_equivalence",
        doc={"a": [[Decimal128("2")]], "b": [[2]]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=[[Decimal128("2")]],
        msg="$setIntersection should apply numeric equivalence to elements inside nested arrays",
    ),
]

# Property [Multiple Arguments]: the intersection generalizes to three or more
# operands, filtering to elements common to all.
SETINTERSECTION_MULTI_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "three_arrays",
        doc={"a": ["a", "b"], "b": ["b", "c"], "c": ["b", "d"]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=["b"],
        msg="$setIntersection should return single common element for three arrays",
    ),
    ExpressionTestCase(
        "three_arrays_common",
        doc={"a": ["red", "blue"], "b": ["green", "blue", "red"], "c": ["red", "blue"]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=["blue", "red"],
        msg="$setIntersection should return two common elements for three arrays",
    ),
    ExpressionTestCase(
        "three_field_refs",
        doc={"a": ["red", "blue"], "b": ["blue", "red", "green"], "c": ["red", "green"]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=["red"],
        msg="$setIntersection should return single common element across three field references",
    ),
    ExpressionTestCase(
        "three_arrays_no_common",
        doc={"a": ["a"], "b": ["b"], "c": ["c"]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[],
        msg="$setIntersection should return empty for three arrays with no common elements",
    ),
    ExpressionTestCase(
        "three_arrays_progressive",
        doc={"a": [1, 2, 3, 4, 5], "b": [2, 3, 4, 5, 6], "c": [3, 4, 5, 6, 7]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[3, 4, 5],
        msg="$setIntersection should return progressively filtered common elements",
    ),
    ExpressionTestCase(
        "four_arrays",
        doc={
            "a": [1, 2, 3, 4, 5],
            "b": [2, 3, 4, 5, 6],
            "c": [3, 4, 5, 6, 7],
            "d": [4, 5, 6, 7, 8],
        },
        expression={"$setIntersection": ["$a", "$b", "$c", "$d"]},
        expected=[4, 5],
        msg="$setIntersection should return progressively filtered common elements for four arrays",
    ),
    ExpressionTestCase(
        "four_arrays_single_common",
        doc={
            "a": ["red", "green"],
            "b": ["blue", "green"],
            "c": ["green", "yellow"],
            "d": ["green"],
        },
        expression={"$setIntersection": ["$a", "$b", "$c", "$d"]},
        expected=["green"],
        msg="$setIntersection should return single common element for four arrays",
    ),
    ExpressionTestCase(
        "four_field_refs_one_empty",
        doc={"a": [], "b": ["blue"], "c": ["red", "blue"], "d": ["red"]},
        expression={"$setIntersection": ["$a", "$b", "$c", "$d"]},
        expected=[],
        msg="$setIntersection should return empty when one of four field references is empty",
    ),
    ExpressionTestCase(
        "five_arrays_no_common",
        doc={
            "a": ["red", "green"],
            "b": ["blue", "green"],
            "c": ["green", "yellow"],
            "d": ["red"],
            "e": ["blue"],
        },
        expression={"$setIntersection": ["$a", "$b", "$c", "$d", "$e"]},
        expected=[],
        msg="$setIntersection should return empty for five arrays with no common element",
    ),
    ExpressionTestCase(
        "five_arrays_all_same",
        doc={"a": ["a"], "b": ["a"], "c": ["a"], "d": ["a"], "e": ["a"]},
        expression={"$setIntersection": ["$a", "$b", "$c", "$d", "$e"]},
        expected=["a"],
        msg="$setIntersection should return a single element for five single-element arrays",
    ),
    ExpressionTestCase(
        "one_empty_among_many",
        doc={"a": [1, 2], "b": [1, 2], "c": []},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[],
        msg="$setIntersection should return empty when one array among many is empty",
    ),
    ExpressionTestCase(
        "three_different_nesting",
        doc={"a": [["red"], ["blue"]], "b": [["red"], ["blue"]], "c": [["red"]]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[["red"]],
        msg="$setIntersection should return the partial nested match across three arrays",
    ),
    ExpressionTestCase(
        "three_no_common_nesting",
        doc={"a": ["red", "green"], "b": ["blue", "green"], "c": [["green"]]},
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=[],
        msg="$setIntersection should return empty for a nesting-level mismatch",
    ),
    ExpressionTestCase(
        "four_no_common_all_arrays",
        doc={"a": [1, 2], "b": [3, 4], "c": [5, 6], "d": [7, 8]},
        expression={"$setIntersection": ["$a", "$b", "$c", "$d"]},
        expected=[],
        msg="$setIntersection should return empty for four arrays with no overlap",
    ),
    ExpressionTestCase(
        "four_with_one_common",
        doc={"a": [1, 2], "b": [1, 4], "c": [1, 3], "d": [1, 4]},
        expression={"$setIntersection": ["$a", "$b", "$c", "$d"]},
        expected=[1],
        msg="$setIntersection should return single common integer for four arrays",
    ),
]

# Property [Arity]: $setIntersection accepts zero or more operands, with zero
# operands yielding an empty result and a single operand yielding its own set.
SETINTERSECTION_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$setIntersection": []},
        expected=[],
        msg="$setIntersection should return empty for zero arguments",
    ),
    ExpressionTestCase(
        "single_array",
        doc={"a": ["a", "b"]},
        expression={"$setIntersection": ["$a"]},
        expected=["a", "b"],
        msg="$setIntersection should return the array itself for a single argument",
    ),
    ExpressionTestCase(
        "single_array_with_dupes",
        doc={"a": [1, 2, 2, 3, 3, 3]},
        expression={"$setIntersection": ["$a"]},
        expected=[1, 2, 3],
        msg="$setIntersection should deduplicate a single array argument",
    ),
]

# Property [Large Arrays]: the operator scales to large operands and still
# deduplicates and intersects correctly.
SETINTERSECTION_LARGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_two",
        doc={"a": list(range(1000)), "b": list(range(50, 1050))},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=list(range(50, 1000)),
        msg="$setIntersection should intersect two 1000-element arrays",
    ),
    ExpressionTestCase(
        "large_three",
        doc={
            "a": list(range(1000)),
            "b": list(range(50, 1050)),
            "c": list(range(100, 1100)),
        },
        expression={"$setIntersection": ["$a", "$b", "$c"]},
        expected=list(range(100, 1000)),
        msg="$setIntersection should intersect three 1000-element arrays",
    ),
    ExpressionTestCase(
        "large_duplicates",
        doc={"a": ["a"] * 10_000, "b": ["a"]},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=["a"],
        msg="$setIntersection should deduplicate 10000 identical elements to a single element",
    ),
    ExpressionTestCase(
        "scale_10k",
        doc={"a": list(range(10_000)), "b": list(range(5_000, 15_000))},
        expression={"$setIntersection": ["$a", "$b"]},
        expected=list(range(5_000, 10_000)),
        msg="$setIntersection should intersect two 10K arrays with 5K overlap",
    ),
]

SETINTERSECTION_CORE_TESTS: list[ExpressionTestCase] = (
    SETINTERSECTION_BASIC_TESTS
    + SETINTERSECTION_EMPTY_TESTS
    + SETINTERSECTION_DUPES_TESTS
    + SETINTERSECTION_ORDER_TESTS
    + SETINTERSECTION_NESTED_TESTS
    + SETINTERSECTION_MULTI_ARG_TESTS
    + SETINTERSECTION_ARITY_TESTS
    + SETINTERSECTION_LARGE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETINTERSECTION_CORE_TESTS))
def test_setIntersection_core(collection, test):
    """Test $setIntersection core behavior with field-reference array operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg, ignore_order=True)
