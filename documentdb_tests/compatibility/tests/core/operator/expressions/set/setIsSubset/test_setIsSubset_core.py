"""Tests for $setIsSubset core subset logic: membership, dedup, ordering, nesting, and scale."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Subset Membership]: the first operand is a subset when every distinct
# element it holds also appears in the second operand.
SETISSUBSET_BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "equal_sets",
        doc={"a": ["a", "b"], "b": ["a", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for equal sets",
    ),
    ExpressionTestCase(
        "proper_subset",
        doc={"a": ["a"], "b": ["a", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a proper subset",
    ),
    ExpressionTestCase(
        "not_subset_extra_elem",
        doc={"a": ["a", "c"], "b": ["a", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for an extra element in the first array",
    ),
    ExpressionTestCase(
        "superset",
        doc={"a": ["a", "b", "c"], "b": ["a", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a superset as the first argument",
    ),
    ExpressionTestCase(
        "disjoint",
        doc={"a": [1, 2, 3], "b": [4, 5, 6]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for disjoint sets",
    ),
    ExpressionTestCase(
        "int_subset",
        doc={"a": [2, 3], "b": [2, 3, 4]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for an int proper subset",
    ),
    ExpressionTestCase(
        "int_equal",
        doc={"a": [1, 2, 3], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for int equal sets",
    ),
    ExpressionTestCase(
        "int_dupes_second",
        doc={"a": [1, 2, 3], "b": [1, 1, 2, 2, 3, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true when duplicates in the second array are ignored",
    ),
]

# Property [Empty Operands]: the empty set is a subset of every set, and only the
# empty set is a subset of the empty set.
SETISSUBSET_EMPTY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_subset_nonempty",
        doc={"a": [], "b": ["a", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for the empty set as a subset of any set",
    ),
    ExpressionTestCase(
        "empty_subset_empty",
        doc={"a": [], "b": []},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for the empty set as a subset of the empty set",
    ),
    ExpressionTestCase(
        "nonempty_not_subset_empty",
        doc={"a": ["a"], "b": []},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a non-empty set as a subset of the empty set",
    ),
    ExpressionTestCase(
        "empty_subset_int",
        doc={"a": [], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for the empty set as a subset of an int array",
    ),
    ExpressionTestCase(
        "int_not_subset_empty",
        doc={"a": [1, 2, 3], "b": []},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a non-empty int set as a subset of the empty set",
    ),
]

# Property [Duplicate Handling]: set semantics ignore repeated elements within
# each operand.
SETISSUBSET_DUPLICATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dupes_first",
        doc={"a": ["a", "a", "b"], "b": ["a", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true when duplicates in the first array are ignored",
    ),
    ExpressionTestCase(
        "dupes_second",
        doc={"a": ["a", "b"], "b": ["a", "a", "b", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true when duplicates in the second array are ignored",
    ),
    ExpressionTestCase(
        "dupes_both",
        doc={"a": ["a", "a"], "b": ["a", "a", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true when duplicates in both arrays are ignored",
    ),
    ExpressionTestCase(
        "heavy_dupes_first",
        doc={"a": [1, 2, 3, 3, 2, 3, 2, 3], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for heavy duplication in the first array",
    ),
    ExpressionTestCase(
        "heavy_dupes_both",
        doc={"a": [1, 2, 3, 3, 2, 3, 2, 3], "b": [1, 2, 3, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for heavy duplication in both arrays",
    ),
    ExpressionTestCase(
        "all_same_subset",
        doc={"a": ["a", "a", "a"], "b": ["a", "a", "a"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for arrays of the same repeated element",
    ),
    ExpressionTestCase(
        "dupes_superset",
        doc={"a": ["b", "a"], "b": ["a", "b", "a"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for duplicates in the second array as a superset",
    ),
    ExpressionTestCase(
        "dupes_both_subset",
        doc={"a": ["b", "b"], "b": ["a", "b", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for duplicates in both arrays as a subset",
    ),
]

# Property [Order Independence]: the result does not depend on element order
# within either operand.
SETISSUBSET_ORDER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "reverse_order_equal",
        doc={"a": ["b", "a"], "b": ["a", "b"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for reverse-order equal sets",
    ),
    ExpressionTestCase(
        "reverse_order_subset",
        doc={"a": ["c", "a"], "b": ["a", "b", "c"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a reverse-order subset",
    ),
    ExpressionTestCase(
        "shuffled_int",
        doc={"a": [2, 3, 1], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a shuffled int order",
    ),
    ExpressionTestCase(
        "shuffled_int_2",
        doc={"a": [2, 1, 3], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for another shuffled int order",
    ),
]

# Property [Directionality]: subset is not commutative, so swapping the operands
# can change the result while symmetric cases still agree.
SETISSUBSET_DIRECTIONALITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "subset_ab",
        doc={"a": [1, 2], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true when the first array is a subset of the second",
    ),
    ExpressionTestCase(
        "subset_ba",
        doc={"a": [1, 2, 3], "b": [1, 2]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false when the operands of a subset pair are swapped",
    ),
    ExpressionTestCase(
        "partial_overlap_ab",
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a partial overlap in one direction",
    ),
    ExpressionTestCase(
        "partial_overlap_ba",
        doc={"a": [2, 3, 4], "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a partial overlap in the other direction",
    ),
    ExpressionTestCase(
        "identical_ab",
        doc={"a": [1, 2], "b": [1, 2]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for identical sets in either direction",
    ),
    ExpressionTestCase(
        "disjoint_ab",
        doc={"a": [1, 2], "b": [3, 4]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for disjoint sets in one direction",
    ),
    ExpressionTestCase(
        "disjoint_ba",
        doc={"a": [3, 4], "b": [1, 2]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for disjoint sets in the other direction",
    ),
]

# Property [Single-Element Arrays]: single-element operands compare by their one
# element.
SETISSUBSET_SINGLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_match",
        doc={"a": [1], "b": [1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a single matching element",
    ),
    ExpressionTestCase(
        "single_no_match",
        doc={"a": [1], "b": [2]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a single non-matching element",
    ),
    ExpressionTestCase(
        "single_in_larger",
        doc={"a": [1], "b": [1, 2, 3, 4, 5]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a single element in a larger set",
    ),
    ExpressionTestCase(
        "identical_strings",
        doc={"a": ["a", "b", "c"], "b": ["a", "b", "c"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for identical string arrays",
    ),
    ExpressionTestCase(
        "identical_diff_order",
        doc={"a": ["c", "b", "a"], "b": ["a", "b", "c"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for identical arrays in a different order",
    ),
    ExpressionTestCase(
        "identical_with_dupes",
        doc={"a": ["a", "a", "b"], "b": ["b", "b", "a"]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for identical arrays with duplicates",
    ),
]

# Property [Atomic Nesting]: nested array elements are compared as whole values
# and are not descended into.
SETISSUBSET_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_match",
        doc={"a": [[1, 2]], "b": [[1, 2], [3, 4]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a nested array element match",
    ),
    ExpressionTestCase(
        "nested_no_match",
        doc={"a": [[1, 2]], "b": [1, 2]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a nested array not in a flat array",
    ),
    ExpressionTestCase(
        "flat_not_in_nested",
        doc={"a": [1, 2], "b": [[1, 2]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for flat elements not in a nested array",
    ),
    ExpressionTestCase(
        "deep_nested",
        doc={"a": [[[1]]], "b": [[[1]], [[2]]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a deeply nested match",
    ),
    ExpressionTestCase(
        "depth_mismatch",
        doc={"a": [[[1]]], "b": [[1]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a nesting depth mismatch",
    ),
    ExpressionTestCase(
        "depth_mismatch_2",
        doc={"a": [[1]], "b": [1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for a nested element not matching a scalar",
    ),
    ExpressionTestCase(
        "nested_order_matters",
        doc={"a": [[1, 2]], "b": [[2, 1]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false when the inner array order differs",
    ),
    ExpressionTestCase(
        "multi_level_scalar",
        doc={"a": ["b", "a"], "b": ["a", "b", ["a"], [["b"]], [[["c"]]]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for scalar elements in a multi-level array",
    ),
    ExpressionTestCase(
        "multi_level_nested",
        doc={"a": ["b", ["a"]], "b": ["a", "b", ["a"], [["b"]], [[["c"]]]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for a nested array element in a multi-level array",
    ),
    ExpressionTestCase(
        "multi_level_deep",
        doc={"a": [[["c"]], [["b"]], ["a"]], "b": ["a", "b", ["a"], [["b"]], [[["c"]]]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for elements at the wrong nesting depth",
    ),
    ExpressionTestCase(
        "multi_level_wrong_depth",
        doc={"a": [[["b"]], [["a"]], ["c"]], "b": ["a", "b", ["a"], [["b"]], [[["c"]]]]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false for elements at the wrong nesting levels",
    ),
]

# Property [Large Arrays]: subset semantics scale to large operands and still
# deduplicate.
SETISSUBSET_LARGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_subset",
        doc={"a": list(range(50)), "b": list(range(100))},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for the first 50 elements as a subset of 100",
    ),
    ExpressionTestCase(
        "large_one_missing",
        doc={"a": list(range(100)), "b": list(range(99))},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=False,
        msg="$setIsSubset should return false when one element is missing from the second array",
    ),
    ExpressionTestCase(
        "large_identical",
        doc={"a": list(range(1000)), "b": list(range(1000))},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for large identical arrays",
    ),
    ExpressionTestCase(
        "large_scale",
        doc={"a": list(range(500)), "b": list(range(1000))},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for 500 elements as a subset of 1000",
    ),
    ExpressionTestCase(
        "heavy_duplication",
        doc={"a": [1] * 10_000, "b": [1]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for 10000 duplicates reduced to a single element",
    ),
    ExpressionTestCase(
        "scale_10k",
        doc={"a": list(range(5000)), "b": list(range(10_000))},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for 5K elements as a subset of 10K",
    ),
    ExpressionTestCase(
        "heavy_duplication_both",
        doc={"a": [1] * 5000 + [2] * 5000, "b": [1, 2, 3]},
        expression={"$setIsSubset": ["$a", "$b"]},
        expected=True,
        msg="$setIsSubset should return true for heavy duplication on both sides",
    ),
]

SETISSUBSET_CORE_TESTS: list[ExpressionTestCase] = (
    SETISSUBSET_BASIC_TESTS
    + SETISSUBSET_EMPTY_TESTS
    + SETISSUBSET_DUPLICATE_TESTS
    + SETISSUBSET_ORDER_TESTS
    + SETISSUBSET_DIRECTIONALITY_TESTS
    + SETISSUBSET_SINGLE_TESTS
    + SETISSUBSET_NESTED_TESTS
    + SETISSUBSET_LARGE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(SETISSUBSET_CORE_TESTS))
def test_setIsSubset_core(collection, test):
    """Test $setIsSubset core subset logic with field-reference array operands."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
