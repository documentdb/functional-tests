"""Tests for $or field path resolution."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

SIMPLE_FIELD_TESTS = [
    ExpressionTestCase(
        "simple_truthy",
        expression={"$or": ["$a"]},
        doc={"a": 1},
        expected=True,
        msg="Should return true for truthy field",
    ),
    ExpressionTestCase(
        "field_refs_true_false",
        expression={"$or": ["$x", "$y"]},
        doc={"x": True, "y": False},
        expected=True,
        msg="Should return true when one field is true",
    ),
]

NESTED_FIELD_TESTS = [
    ExpressionTestCase(
        "nested_field_true",
        expression={"$or": ["$a.b"]},
        doc={"a": {"b": True}},
        expected=True,
        msg="Should return true for nested true field",
    ),
    ExpressionTestCase(
        "deep_nested_path",
        expression={"$or": ["$a.b.c.d"]},
        doc={"a": {"b": {"c": {"d": True}}}},
        expected=True,
        msg="Should return true for deep nested truthy path",
    ),
]

ARRAY_INDEX_TESTS = [
    ExpressionTestCase(
        "array_index_truthy",
        expression={"$or": ["$a.0"]},
        doc={"a": [10, 0, 30]},
        expected=True,
        msg="$a.0 in aggregation resolves to array (truthy)",
    ),
]

MISSING_FIELD_TESTS = [
    ExpressionTestCase(
        "nonexistent",
        expression={"$or": ["$nonexistent"]},
        doc={"a": 1},
        expected=False,
        msg="Should return false for non-existent field",
    ),
]

ARRAY_VALUE_TESTS = [
    ExpressionTestCase(
        "field_is_array",
        expression={"$or": ["$a"]},
        doc={"a": [0, None, False]},
        expected=True,
        msg="Should return true when field is array (truthy)",
    ),
]

ALL_TESTS = (
    SIMPLE_FIELD_TESTS
    + NESTED_FIELD_TESTS
    + ARRAY_INDEX_TESTS
    + MISSING_FIELD_TESTS
    + ARRAY_VALUE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_or_field_path(collection, test):
    """Test $or field path resolution."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
