"""Tests for $cond missing field behavior, null handling, and $$REMOVE patterns."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

MISSING_AND_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "obj_missing_if_field",
        expression={"$cond": {"if": "$inv", "then": "yes", "else": "no"}},
        doc={"x": 1},
        expected="no",
        msg="Missing field → else (object syntax)",
    ),
    ExpressionTestCase(
        "arr_missing_if_field",
        expression={"$cond": ["$inv", "yes", "no"]},
        doc={"x": 1},
        expected="no",
        msg="Missing field → else (array syntax)",
    ),
    ExpressionTestCase(
        "null_condition_literal",
        expression={"$cond": {"if": None, "then": "yes", "else": "no"}},
        doc={"x": 1},
        expected="no",
        msg="null condition → else",
    ),
    ExpressionTestCase(
        "null_in_then",
        expression={"$cond": {"if": True, "then": None, "else": "no"}},
        doc={"x": 1},
        expected=None,
        msg="null in then → null",
    ),
    ExpressionTestCase(
        "null_in_else",
        expression={"$cond": {"if": False, "then": "yes", "else": None}},
        doc={"x": 1},
        expected=None,
        msg="null in else → null",
    ),
    ExpressionTestCase(
        "null_field_condition",
        expression={"$cond": {"if": "$a", "then": "yes", "else": "no"}},
        doc={"a": None},
        expected="no",
        msg="null field → else",
    ),
    ExpressionTestCase(
        "missing_field_vs_null_condition",
        expression={"$cond": {"if": "$a", "then": "yes", "else": "no"}},
        doc={"b": 1},
        expected="no",
        msg="missing field is falsy",
    ),
    ExpressionTestCase(
        "null_field_in_then",
        expression={"$cond": {"if": True, "then": "$a", "else": "fallback"}},
        doc={"a": None},
        expected=None,
        msg="null-valued field in then → null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MISSING_AND_NULL_TESTS))
def test_cond_missing_and_null(collection, test):
    """Test $cond missing field behavior and null handling."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_cond_missing_field_in_then(collection):
    """Test $cond with missing field in then — field excluded from output."""
    result = execute_expression_with_insert(
        collection, {"$cond": {"if": True, "then": "$missing", "else": "fallback"}}, {"x": 1}
    )
    assertSuccess(result, [{}], msg="missing field in then → field excluded from output")


def test_cond_remove_evaluated_when_selected(collection):
    """Test $cond with $$REMOVE selected — field excluded from output."""
    result = execute_expression_with_insert(
        collection, {"$cond": {"if": True, "then": "$$REMOVE", "else": "kept"}}, {"x": 1}
    )
    assertSuccess(result, [{}], msg="$$REMOVE selected → field excluded from output")
