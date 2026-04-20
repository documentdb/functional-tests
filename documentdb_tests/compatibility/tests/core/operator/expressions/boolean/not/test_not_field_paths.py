"""Tests for $not with field paths, nested paths, array values, and expression wrapping."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

FIELD_PATH_TESTS = [
    ExpressionTestCase(
        "not_field_true",
        expression={"$not": ["$a"]},
        doc={"a": True},
        expected=False,
        msg="$not([$a]) should return false when a=true",
    ),
    ExpressionTestCase(
        "not_field_false",
        expression={"$not": ["$a"]},
        doc={"a": False},
        expected=True,
        msg="$not([$a]) should return true when a=false",
    ),
]

NESTED_PATH_TESTS = [
    ExpressionTestCase(
        "not_field_deep_nested_truthy",
        expression={"$not": ["$a.b.c.d"]},
        doc={"a": {"b": {"c": {"d": True}}}},
        expected=False,
        msg="$not([$a.b.c.d]) should return false for deep nested truthy path",
    ),
    ExpressionTestCase(
        "not_field_deep_nested_falsy",
        expression={"$not": ["$a.b.c.d"]},
        doc={"a": {"b": {"c": {"d": 0}}}},
        expected=True,
        msg="$not([$a.b.c.d]) should return true for deep nested falsy path",
    ),
]

ARRAY_INDEX_TESTS = [
    ExpressionTestCase(
        "not_field_array_index_truthy",
        expression={"$not": ["$a.0"]},
        doc={"a": [10, 0, 30]},
        expected=False,
        msg="$not([$a.0]) should return false, array resolved value is truthy",
    ),
]

ARRAY_VALUE_TESTS = [
    ExpressionTestCase(
        "not_field_empty_array",
        expression={"$not": ["$a"]},
        doc={"a": []},
        expected=False,
        msg="$not([$a]) should return false when a=[], empty arrays are truthy",
    ),
    ExpressionTestCase(
        "not_field_composite_array",
        expression={"$not": ["$a.b"]},
        doc={"a": [{"b": 1}, {"b": 2}]},
        expected=False,
        msg="$not([$a.b]) should return false, array traversal yields [1,2], truthy",
    ),
    ExpressionTestCase(
        "not_field_array_all_falsy",
        expression={"$not": ["$a"]},
        doc={"a": [0, None, False]},
        expected=False,
        msg="$not([$a]) should return false, array itself is truthy even if contents are falsy",
    ),
]

EXPRESSION_WRAPPING_TESTS = [
    ExpressionTestCase(
        "not_field_wrapping_truthy_divide",
        expression={"$not": [{"$divide": [1, "$x"]}]},
        doc={"x": 2},
        expected=False,
        msg="$not wrapping truthy $divide result (0.5) returns false",
    ),
    ExpressionTestCase(
        "not_field_wrapping_gt_true",
        expression={"$not": [{"$gt": ["$x", 0]}]},
        doc={"x": 10},
        expected=False,
        msg="$not wrapping true $gt returns false",
    ),
    ExpressionTestCase(
        "not_field_wrapping_gt_false",
        expression={"$not": [{"$gt": ["$x", 100]}]},
        doc={"x": 10},
        expected=True,
        msg="$not wrapping false $gt returns true",
    ),
]

ALL_TESTS = (
    FIELD_PATH_TESTS
    + NESTED_PATH_TESTS
    + ARRAY_INDEX_TESTS
    + ARRAY_VALUE_TESTS
    + EXPRESSION_WRAPPING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_not_field_paths(collection, test):
    """Test $not with field paths, nested paths, array values, and expression wrapping."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
