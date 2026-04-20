"""
Tests for $eq array and object comparisons.

Covers array ordering, nested arrays, object key order, array vs scalar,
and aggregation $eq vs query $eq behavior differences.
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

ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_arrays", expression={"$eq": [[], []]}, expected=True, msg="Empty arrays equal"
    ),
    ExpressionTestCase(
        "same_arrays", expression={"$eq": [[1, 2], [1, 2]]}, expected=True, msg="Same arrays equal"
    ),
    ExpressionTestCase(
        "diff_order",
        expression={"$eq": [[1, 2], [2, 1]]},
        expected=False,
        msg="Different order not equal",
    ),
    ExpressionTestCase(
        "diff_length",
        expression={"$eq": [[1], [1, 2]]},
        expected=False,
        msg="Different length not equal",
    ),
    ExpressionTestCase(
        "array_vs_scalar",
        expression={"$eq": [[1], 1]},
        expected=False,
        msg="Single-element array [1] not equal to literal 1 in aggregation $eq",
    ),
    ExpressionTestCase(
        "empty_array_vs_null",
        expression={"$eq": [[], None]},
        expected=False,
        msg="Empty array not equal to null (null < [] in BSON ordering)",
    ),
    ExpressionTestCase(
        "empty_vs_null_elem",
        expression={"$eq": [[], [None]]},
        expected=False,
        msg="Empty array not equal to [null]",
    ),
    ExpressionTestCase(
        "null_elems",
        expression={"$eq": [[None], [None]]},
        expected=True,
        msg="[null] equals [null]",
    ),
    ExpressionTestCase(
        "type_in_array",
        expression={"$eq": [[0], [False]]},
        expected=False,
        msg="Array [0] not equal to [false]",
    ),
    ExpressionTestCase(
        "nested_same",
        expression={"$eq": [[[1, 2], [3, 4]], [[1, 2], [3, 4]]]},
        expected=True,
        msg="Nested arrays equal",
    ),
    ExpressionTestCase(
        "nested_diff_order",
        expression={"$eq": [[[1, 2], [3, 4]], [[3, 4], [1, 2]]]},
        expected=False,
        msg="Nested arrays different order not equal",
    ),
]


OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_objects", expression={"$eq": [{}, {}]}, expected=True, msg="Empty objects equal"
    ),
    ExpressionTestCase(
        "same_objects",
        expression={"$eq": [{"a": 1}, {"a": 1}]},
        expected=True,
        msg="Same objects equal",
    ),
    ExpressionTestCase(
        "diff_key_order",
        expression={"$eq": [{"a": 1, "b": 2}, {"b": 2, "a": 1}]},
        expected=False,
        msg="Different key order not equal",
    ),
    ExpressionTestCase(
        "diff_values",
        expression={"$eq": [{"a": 1}, {"a": 2}]},
        expected=False,
        msg="Different values not equal",
    ),
    ExpressionTestCase(
        "diff_keys",
        expression={"$eq": [{"a": 1}, {"b": 1}]},
        expected=False,
        msg="Different keys not equal",
    ),
    ExpressionTestCase(
        "nested_same",
        expression={"$eq": [{"a": {"b": 1}}, {"a": {"b": 1}}]},
        expected=True,
        msg="Nested objects equal",
    ),
    ExpressionTestCase(
        "nested_diff_val",
        expression={"$eq": [{"a": {"b": 1}}, {"a": {"b": 2}}]},
        expected=False,
        msg="Nested objects different value not equal",
    ),
    ExpressionTestCase(
        "nested_diff_key_order",
        expression={"$eq": [{"a": {"b": 1, "c": 2}}, {"a": {"c": 2, "b": 1}}]},
        expected=False,
        msg="Nested objects different key order not equal",
    ),
]


ALL_TESTS = ARRAY_TESTS + OBJECT_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_literal(collection, test):
    """Test $eq literal comparisons for arrays, objects, and empty/null edge cases."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


ARRAY_VS_SCALAR_AGG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_field_vs_scalar",
        expression={"$eq": ["$a", 1]},
        doc={"a": [1, 2, 3]},
        expected=False,
        msg="Array field not equal to scalar in aggregation $eq",
    ),
    ExpressionTestCase(
        "array_field_vs_whole_array",
        expression={"$eq": ["$a", [1, 2, 3]]},
        doc={"a": [1, 2, 3]},
        expected=True,
        msg="Array field equals whole array",
    ),
    ExpressionTestCase(
        "array_field_vs_diff_length",
        expression={"$eq": ["$a", [1, 2]]},
        doc={"a": [1, 2, 3]},
        expected=False,
        msg="Array field not equal to different length array",
    ),
    ExpressionTestCase(
        "array_field_vs_diff_order",
        expression={"$eq": ["$a", [3, 2, 1]]},
        doc={"a": [1, 2, 3]},
        expected=False,
        msg="Array field not equal to different order array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_VS_SCALAR_AGG_TESTS))
def test_eq_array_vs_scalar_aggregation(collection, test):
    """Test $eq array vs scalar in aggregation context (no element-wise matching)."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
