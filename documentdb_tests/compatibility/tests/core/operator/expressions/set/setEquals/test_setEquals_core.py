"""Tests for $setEquals core set-equality behavior: dedup, ordering, nesting, and arity."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Basic Equality]: two operands are equal when they hold the same set
# of distinct elements, independent of order or repetition.
SETEQUALS_BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "identical_ints",
        doc={"a": [1, 2, 3], "b": [1, 2, 3]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for identical arrays",
    ),
    ExpressionTestCase(
        "different_elements",
        doc={"a": [1, 2, 3], "b": [1, 2, 4]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for different elements",
    ),
    ExpressionTestCase(
        "partial_overlap",
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for partial overlap",
    ),
    ExpressionTestCase(
        "disjoint",
        doc={"a": [1, 2, 3], "b": [4, 5, 6]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for disjoint arrays",
    ),
    ExpressionTestCase(
        "first_superset",
        doc={"a": [1, 2, 3], "b": [2, 3]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false when a superset is compared to a subset",
    ),
    ExpressionTestCase(
        "first_subset",
        doc={"a": [2, 3], "b": [2, 3, 4]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false when a subset is compared to a superset",
    ),
    ExpressionTestCase(
        "strings_equal",
        doc={"a": ["red", "blue"], "b": ["blue", "red"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for string arrays with the same elements",
    ),
    ExpressionTestCase(
        "strings_not_equal",
        doc={"a": ["red", "blue"], "b": ["green", "red"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for different string elements",
    ),
    ExpressionTestCase(
        "strings_extra_in_second",
        doc={"a": ["red", "blue"], "b": ["red", "blue", "green"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for an extra element in the second array",
    ),
    ExpressionTestCase(
        "strings_extra_in_first",
        doc={"a": ["red", "blue", "green"], "b": ["blue", "red"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for an extra element in the first array",
    ),
    ExpressionTestCase(
        "second_empty",
        doc={"a": ["red", "blue"], "b": []},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for a non-empty array versus an empty array",
    ),
    ExpressionTestCase(
        "mixed_types_equal",
        doc={"a": [1, "a", True], "b": ["a", True, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for mixed types with the same elements",
    ),
    ExpressionTestCase(
        "mixed_types_not_equal",
        doc={"a": [1, "a", True], "b": ["a", True, 2]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for mixed types with different elements",
    ),
]

# Property [Empty Operands]: empty arrays are equal only to other empty arrays.
SETEQUALS_EMPTY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "both_empty",
        doc={"a": [], "b": []},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for two empty arrays",
    ),
    ExpressionTestCase(
        "first_empty",
        doc={"a": [], "b": [1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for an empty array versus a non-empty array",
    ),
    ExpressionTestCase(
        "second_empty_int",
        doc={"a": [1], "b": []},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for a non-empty array versus an empty array",
    ),
    ExpressionTestCase(
        "three_all_empty",
        doc={"a": [], "b": [], "c": []},
        expression={"$setEquals": ["$a", "$b", "$c"]},
        expected=True,
        msg="$setEquals should return true for three empty arrays",
    ),
]

# Property [Duplicate Handling]: set semantics ignore repeated elements within
# each operand.
SETEQUALS_DUPLICATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dupes_in_second",
        doc={"a": ["a", "b"], "b": ["a", "b", "a"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true when duplicates in the second array are ignored",
    ),
    ExpressionTestCase(
        "dupes_in_first",
        doc={"a": ["a", "a", "a"], "b": ["a"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true when duplicates in the first array are ignored",
    ),
    ExpressionTestCase(
        "heavy_dupes_both",
        doc={"a": [1, 1, 2, 2, 3, 3], "b": [3, 2, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true when heavy duplicates are ignored",
    ),
    ExpressionTestCase(
        "same_dupes_both",
        doc={"a": [1, 1, 1], "b": [1, 1, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for the same duplicates in both arrays",
    ),
    ExpressionTestCase(
        "different_dupe_counts",
        doc={"a": [1, 2, 2, 3], "b": [1, 2, 3, 3]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for different duplicate counts of the same set",
    ),
    ExpressionTestCase(
        "string_heavy_dupes",
        doc={"a": ["red", "red", "red"], "b": ["red"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true when string duplicates are ignored",
    ),
    ExpressionTestCase(
        "string_dupes_three_args",
        doc={
            "a": ["red", "blue", "blue"],
            "b": ["red", "red", "red", "blue", "blue"],
            "c": ["red", "blue", "red", "blue"],
        },
        expression={"$setEquals": ["$a", "$b", "$c"]},
        expected=True,
        msg="$setEquals should return true when string duplicates across three arrays are ignored",
    ),
    ExpressionTestCase(
        "dupes_not_equal",
        doc={
            "a": ["red", "red", "red", "blue", "blue"],
            "b": ["red", "red"],
            "c": ["blue", "blue"],
        },
        expression={"$setEquals": ["$a", "$b", "$c"]},
        expected=False,
        msg="$setEquals should return false for different distinct elements despite duplicates",
    ),
    ExpressionTestCase(
        "field_dupes_equal",
        doc={"a": [1, 2, 2, 2, 2], "b": [1, 2, 1, 1, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true when duplicates reduce to the same distinct elements",
    ),
    ExpressionTestCase(
        "field_paths_with_dupes",
        doc={"a": [1, 2, 3], "b": [1, 1, 2, 2, 3, 3]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true when duplicates in one operand reduce to the other set",
    ),
]

# Property [Order Independence]: the result does not depend on element order
# within an operand.
SETEQUALS_ORDER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_order",
        doc={"a": [1, 2, 3], "b": [3, 2, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true regardless of integer order",
    ),
    ExpressionTestCase(
        "string_order",
        doc={"a": ["c", "b", "a"], "b": ["a", "b", "c"]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true regardless of string order",
    ),
    ExpressionTestCase(
        "mixed_order",
        doc={"a": [True, 1, "a"], "b": ["a", True, 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true regardless of mixed-type order",
    ),
]

# Property [Atomic Nesting]: nested array elements are compared as whole values
# and are not descended into.
SETEQUALS_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_nested",
        doc={"a": [[1, 2]], "b": [[1, 2]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for the same nested array element",
    ),
    ExpressionTestCase(
        "nested_inner_order_differs",
        doc={"a": [[1, 2]], "b": [[2, 1]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for different inner order in an atomic comparison",
    ),
    ExpressionTestCase(
        "nested_set_of_arrays",
        doc={"a": [[1], [2]], "b": [[2], [1]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for the same set of nested arrays",
    ),
    ExpressionTestCase(
        "nested_mixed_scalar",
        doc={"a": [[1, 2], 3], "b": [3, [1, 2]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for mixed nested and scalar elements",
    ),
    ExpressionTestCase(
        "nested_vs_flat",
        doc={"a": [[1, 2]], "b": [1, 2]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for a nested array versus flat elements",
    ),
    ExpressionTestCase(
        "nested_reorder",
        doc={"a": [1, [2, 3]], "b": [[2, 3], 1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for reordered nested and scalar elements",
    ),
    ExpressionTestCase(
        "nested_strings_same",
        doc={"a": [["red", "blue"]], "b": [["red", "blue"]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for the same nested string array",
    ),
    ExpressionTestCase(
        "nested_strings_inner_order",
        doc={"a": [["red", "blue"]], "b": [["blue", "red"]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for different inner string order",
    ),
    ExpressionTestCase(
        "nested_vs_flat_strings",
        doc={"a": ["red", "blue"], "b": [["red"], ["blue"]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for flat strings versus nested arrays",
    ),
    ExpressionTestCase(
        "dup_nested",
        doc={"a": [[1, 2], [1, 2]], "b": [[1, 2]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true when duplicate nested arrays are deduplicated",
    ),
    ExpressionTestCase(
        "dup_nested_multi",
        doc={"a": [[1, 2], [3, 4]], "b": [[3, 4], [1, 2], [1, 2]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should deduplicate duplicate nested arrays in the second array",
    ),
    ExpressionTestCase(
        "deeply_nested_same",
        doc={"a": [[[1]]], "b": [[[1]]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for deeply nested same elements",
    ),
    ExpressionTestCase(
        "deeply_nested_diff",
        doc={"a": [[[1]]], "b": [[[2]]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for deeply nested different elements",
    ),
    ExpressionTestCase(
        "very_deeply_nested",
        doc={"a": [[[[1]]]], "b": [[[[1]]]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for very deeply nested same elements",
    ),
    ExpressionTestCase(
        "different_nesting_depth",
        doc={"a": [["red", "blue"]], "b": [[["red", "blue"]]]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for different nesting depth",
    ),
]

# Property [Single-Element Arrays]: single-element operands compare by their one
# element, including special scalar values.
SETEQUALS_SINGLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_equal",
        doc={"a": [1], "b": [1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for single equal elements",
    ),
    ExpressionTestCase(
        "single_not_equal",
        doc={"a": [1], "b": [2]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for single different elements",
    ),
    ExpressionTestCase(
        "single_null",
        doc={"a": [None], "b": [None]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for single null elements",
    ),
    ExpressionTestCase(
        "single_false",
        doc={"a": [False], "b": [False]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for single false elements",
    ),
    ExpressionTestCase(
        "single_empty_string",
        doc={"a": [""], "b": [""]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for single empty-string elements",
    ),
]

# Property [Multiple Arguments]: equality generalizes to three or more operands,
# holding only when every operand shares the same set.
SETEQUALS_MULTI_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "three_equal",
        doc={"a": [1, 2], "b": [2, 1], "c": [1, 2]},
        expression={"$setEquals": ["$a", "$b", "$c"]},
        expected=True,
        msg="$setEquals should return true for three equal arrays",
    ),
    ExpressionTestCase(
        "three_one_differs",
        doc={"a": [1, 2], "b": [2, 1], "c": [1, 3]},
        expression={"$setEquals": ["$a", "$b", "$c"]},
        expected=False,
        msg="$setEquals should return false for three arrays when one differs",
    ),
    ExpressionTestCase(
        "five_equal",
        doc={"a": [1], "b": [1], "c": [1], "d": [1], "e": [1]},
        expression={"$setEquals": ["$a", "$b", "$c", "$d", "$e"]},
        expected=True,
        msg="$setEquals should return true for five equal arrays",
    ),
    ExpressionTestCase(
        "five_last_differs",
        doc={"a": [1], "b": [1], "c": [1], "d": [1], "e": [2]},
        expression={"$setEquals": ["$a", "$b", "$c", "$d", "$e"]},
        expected=False,
        msg="$setEquals should return false for five arrays when the last differs",
    ),
    ExpressionTestCase(
        "three_with_dupes",
        doc={"a": [1, 2], "b": [2, 1], "c": [1, 2, 1]},
        expression={"$setEquals": ["$a", "$b", "$c"]},
        expected=True,
        msg="$setEquals should return true for three arrays with duplicates",
    ),
    ExpressionTestCase(
        "three_second_differs",
        doc={"a": [1, 2], "b": [2, 3], "c": [1, 2]},
        expression={"$setEquals": ["$a", "$b", "$c"]},
        expected=False,
        msg="$setEquals should return false for three arrays when the second differs",
    ),
    ExpressionTestCase(
        "three_empty_one_not",
        doc={"a": [], "b": [], "c": [1]},
        expression={"$setEquals": ["$a", "$b", "$c"]},
        expected=False,
        msg="$setEquals should return false for two empty arrays and one non-empty array",
    ),
    ExpressionTestCase(
        "four_all_reduce_same",
        doc={"a": [1, 2], "b": [2, 1], "c": [1, 1, 2], "d": [1, 2, 2]},
        expression={"$setEquals": ["$a", "$b", "$c", "$d"]},
        expected=True,
        msg="$setEquals should return true for four arrays all reducing to the same set",
    ),
    ExpressionTestCase(
        "four_args_not_equal",
        doc={"a": [1, 2], "b": [1, 2, 3, 4], "c": [5, 6], "d": [1, 8]},
        expression={"$setEquals": ["$a", "$b", "$c", "$d"]},
        expected=False,
        msg="$setEquals should return false for four different arrays",
    ),
]

# Property [Large Arrays]: equality scales to large operands and still applies
# set semantics.
SETEQUALS_LARGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_identical",
        doc={"a": list(range(1000)), "b": list(range(999, -1, -1))},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for large identical arrays in different order",
    ),
    ExpressionTestCase(
        "large_last_differs",
        doc={"a": list(range(1000)), "b": list(range(999)) + [9999]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=False,
        msg="$setEquals should return false for large arrays with one different element",
    ),
    ExpressionTestCase(
        "large_heavy_dupes",
        doc={"a": [1] * 10_000, "b": [1]},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for 10000 duplicates equal to a single element",
    ),
    ExpressionTestCase(
        "scale_10k",
        doc={"a": list(range(10_000)), "b": list(range(9999, -1, -1))},
        expression={"$setEquals": ["$a", "$b"]},
        expected=True,
        msg="$setEquals should return true for 10K elements reversed",
    ),
    ExpressionTestCase(
        "large_variadic",
        doc={"a": [1, 2], "b": [2, 1], "c": [1, 2], "d": [2, 1], "e": [1, 2]},
        expression={"$setEquals": ["$a", "$b", "$c", "$d", "$e"]},
        expected=True,
        msg="$setEquals should return true for many variadic equal arrays",
    ),
]

SETEQUALS_CORE_TESTS: list[ExpressionTestCase] = (
    SETEQUALS_BASIC_TESTS
    + SETEQUALS_EMPTY_TESTS
    + SETEQUALS_DUPLICATE_TESTS
    + SETEQUALS_ORDER_TESTS
    + SETEQUALS_NESTED_TESTS
    + SETEQUALS_SINGLE_TESTS
    + SETEQUALS_MULTI_ARG_TESTS
    + SETEQUALS_LARGE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETEQUALS_CORE_TESTS))
def test_setEquals_core(collection, test):
    """Test $setEquals core set-equality behavior with field-reference array operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
