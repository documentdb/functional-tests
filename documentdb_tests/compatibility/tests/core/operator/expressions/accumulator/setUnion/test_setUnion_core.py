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

# Property [Core Set Union Behavior]: the union of arrays contains all unique
# elements from all inputs, with both intra-array and inter-array duplicates
# removed.
SETUNION_CORE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "core_disjoint",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should contain all elements from disjoint arrays",
    ),
    ExpressionTestCase(
        "core_overlapping",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should contain each shared element only once",
    ),
    ExpressionTestCase(
        "core_intra_duplicates",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1, 1, 2, 2, 3]},
        expected=[1, 2, 3],
        msg="$setUnion should deduplicate within a single array",
    ),
    ExpressionTestCase(
        "core_intra_and_inter_duplicates",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [1, 1, 2], "b": [2, 3, 3]},
        expected=[1, 2, 3],
        msg="$setUnion should remove both intra-array and inter-array duplicates",
    ),
    ExpressionTestCase(
        "core_three_arrays",
        expression={"$setUnion": ["$a", "$b", "$c"]},
        doc={"a": [1, 2], "b": [2, 3], "c": [3, 4]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should handle three overlapping arrays",
    ),
    ExpressionTestCase(
        "core_large_overlap",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": list(range(1000)), "b": list(range(500, 1500))},
        expected=list(range(1500)),
        msg="$setUnion should handle large arrays with overlap",
    ),
]

# Property [Identity]: the empty array is the identity element for set union.
SETUNION_IDENTITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "identity_empty_with_values",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [1, 2, 3], "b": []},
        expected=[1, 2, 3],
        msg="$setUnion of an array with [] should return the unique elements of that array",
    ),
    ExpressionTestCase(
        "identity_values_with_empty",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [], "b": [4, 5]},
        expected=[4, 5],
        msg="$setUnion of [] with an array should return the unique elements of that array",
    ),
    ExpressionTestCase(
        "identity_empty_with_duplicates",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [1, 1, 2], "b": []},
        expected=[1, 2],
        msg="$setUnion of an array with duplicates and [] should return deduplicated elements",
    ),
    ExpressionTestCase(
        "identity_two_empties",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [], "b": []},
        expected=[],
        msg="$setUnion of two empty arrays should return []",
    ),
]

# Property [Nested Arrays as Elements]: nested arrays are treated as opaque
# elements and are not flattened; identical nested arrays are deduplicated by
# value and element order.
SETUNION_NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_not_flattened",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": ["a", "b"], "b": [["a", "b"]]},
        expected=["a", "b", ["a", "b"]],
        msg="$setUnion should treat a nested array as a distinct element, not flatten it",
    ),
    ExpressionTestCase(
        "nested_deeply_nested",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [[1, 2]], "b": [[[1, 2]]]},
        expected=[[1, 2], [[1, 2]]],
        msg="$setUnion should treat deeply nested arrays as opaque elements",
    ),
    ExpressionTestCase(
        "nested_identical_dedup",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [[1, 2]], "b": [[1, 2]]},
        expected=[[1, 2]],
        msg="$setUnion should deduplicate identical nested arrays",
    ),
    ExpressionTestCase(
        "nested_different_order_distinct",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [[1, 2]], "b": [[2, 1]]},
        expected=[[1, 2], [2, 1]],
        msg="$setUnion should treat nested arrays with different element order as distinct",
    ),
]

# Property [Self-Union]: union of an array with itself returns the
# deduplicated contents of that array.
SETUNION_SELF_UNION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "self_distinct_elements",
        expression={"$setUnion": ["$a", "$a"]},
        doc={"a": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="$setUnion of a distinct-element array with itself should equal its contents",
    ),
    ExpressionTestCase(
        "self_with_duplicates",
        expression={"$setUnion": ["$a", "$a"]},
        doc={"a": [1, 1, 2, 3, 3]},
        expected=[1, 2, 3],
        msg="$setUnion of an array with duplicates unioned with itself should deduplicate",
    ),
    ExpressionTestCase(
        "self_empty",
        expression={"$setUnion": ["$a", "$a"]},
        doc={"a": []},
        expected=[],
        msg="$setUnion of an empty array with itself should return []",
    ),
]

# Property [Commutativity (Value)]: the set of elements in the result is the
# same regardless of argument order.
SETUNION_COMMUTATIVITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "comm_overlapping_ab",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [1, 2, 3], "b": [2, 3, 4]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should produce the same set when arrays overlap (a,b)",
    ),
    ExpressionTestCase(
        "comm_overlapping_ba",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [2, 3, 4], "b": [1, 2, 3]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should produce the same set when arrays overlap (b,a)",
    ),
    ExpressionTestCase(
        "comm_overlapping_reversed_elements",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [3, 2, 1], "b": [4, 3, 2]},
        expected=[1, 2, 3, 4],
        msg="$setUnion should produce the same set with reversed element order",
    ),
]

SETUNION_CORE_TESTS_ALL = (
    SETUNION_CORE_TESTS
    + SETUNION_IDENTITY_TESTS
    + SETUNION_NESTED_ARRAY_TESTS
    + SETUNION_SELF_UNION_TESTS
    + SETUNION_COMMUTATIVITY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_CORE_TESTS_ALL))
def test_setunion_core(collection, test_case: ExpressionTestCase):
    """Test $setUnion core behavior cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_order=True,
    )
