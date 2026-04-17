"""
Integration tests for set expression operators interacting with each other.

These tests verify that composing multiple set operators produces correct
results. Individual operator edge cases are tested in each operator's own
folder; these tests focus on cross-operator interactions where behavioral
differences between engines are most likely to surface.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Union Size]: $size of $setUnion equals the number of distinct
# elements across the input arrays.
UNION_SIZE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_of_union_disjoint",
        expression={"$size": {"$setUnion": ["$a", "$b"]}},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=4,
        msg="$size of $setUnion of disjoint arrays should equal total element count",
    ),
    ExpressionTestCase(
        "size_of_union_overlapping",
        expression={"$size": {"$setUnion": ["$a", "$b"]}},
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expected=4,
        msg="$size of $setUnion of overlapping arrays should equal distinct count",
    ),
    ExpressionTestCase(
        "size_of_union_identical",
        expression={"$size": {"$setUnion": ["$a", "$b"]}},
        doc={"a": [1, 2, 3], "b": [1, 2, 3]},
        expected=3,
        msg="$size of $setUnion of identical arrays should equal single array size",
    ),
    ExpressionTestCase(
        "size_of_union_empty",
        expression={"$size": {"$setUnion": ["$a", "$b"]}},
        doc={"a": [], "b": []},
        expected=0,
        msg="$size of $setUnion of empty arrays should be 0",
    ),
]

# Property [Union-Intersection Subset]: $setIntersection of $setUnion(A, B)
# with A always equals A (since A is a subset of A ∪ B).
UNION_INTERSECTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "intersect_union_with_operand_disjoint",
        expression={"$setIntersection": [{"$setUnion": ["$a", "$b"]}, "$a"]},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=[1, 2],
        msg="$setIntersection of $setUnion(A, B) with A should equal A for disjoint sets",
    ),
    ExpressionTestCase(
        "intersect_union_with_operand_overlapping",
        expression={"$setIntersection": [{"$setUnion": ["$a", "$b"]}, "$a"]},
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expected=[1, 2, 3],
        msg="$setIntersection of $setUnion(A, B) with A should equal A for overlapping sets",
    ),
    ExpressionTestCase(
        "intersect_union_with_third",
        expression={"$setIntersection": [{"$setUnion": ["$a", "$b"]}, "$c"]},
        doc={"a": [1, 2], "b": [3, 4], "c": [2, 3, 5]},
        expected=[2, 3],
        msg="$setIntersection of $setUnion(A, B) with C should return common elements",
    ),
]

# Property [Union Complement]: $setDifference of $setUnion(A, B) minus A
# yields the elements unique to B.
UNION_DIFFERENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "difference_union_minus_operand_disjoint",
        expression={"$setDifference": [{"$setUnion": ["$a", "$b"]}, "$a"]},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=[3, 4],
        msg="$setDifference of $setUnion(A, B) minus A should equal B for disjoint sets",
    ),
    ExpressionTestCase(
        "difference_union_minus_operand_overlapping",
        expression={"$setDifference": [{"$setUnion": ["$a", "$b"]}, "$a"]},
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expected=[4],
        msg="$setDifference of $setUnion(A, B) minus A should yield elements unique to B",
    ),
]

# Property [Union Commutativity]: $setUnion(A, B) equals $setUnion(B, A).
UNION_COMMUTATIVITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "commutativity_disjoint",
        expression={"$setEquals": [{"$setUnion": ["$a", "$b"]}, {"$setUnion": ["$b", "$a"]}]},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=True,
        msg="$setUnion(A, B) should equal $setUnion(B, A) for disjoint sets",
    ),
    ExpressionTestCase(
        "commutativity_overlapping",
        expression={"$setEquals": [{"$setUnion": ["$a", "$b"]}, {"$setUnion": ["$b", "$a"]}]},
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expected=True,
        msg="$setUnion(A, B) should equal $setUnion(B, A) for overlapping sets",
    ),
]

# Property [Union Superset]: A is always a subset of $setUnion(A, B).
UNION_SUBSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "subset_operand_of_union_disjoint",
        expression={"$setIsSubset": ["$a", {"$setUnion": ["$a", "$b"]}]},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=True,
        msg="A should be a subset of $setUnion(A, B) for disjoint sets",
    ),
    ExpressionTestCase(
        "subset_operand_of_union_overlapping",
        expression={"$setIsSubset": ["$a", {"$setUnion": ["$a", "$b"]}]},
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expected=True,
        msg="A should be a subset of $setUnion(A, B) for overlapping sets",
    ),
]

SET_COMBINATION_TESTS = (
    UNION_SIZE_TESTS
    + UNION_INTERSECTION_TESTS
    + UNION_DIFFERENCE_TESTS
    + UNION_COMMUTATIVITY_TESTS
    + UNION_SUBSET_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SET_COMBINATION_TESTS))
def test_set_combination(collection, test_case: ExpressionTestCase):
    """Test set operator combinations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        ignore_order=True,
    )
