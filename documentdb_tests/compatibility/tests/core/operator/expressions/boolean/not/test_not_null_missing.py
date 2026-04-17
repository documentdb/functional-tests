"""Tests for $not with null and missing field behavior."""

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

NULL_LITERAL_TESTS = [
    ExpressionTestCase(
        "not_null_literal_null",
        expression={"$not": [None]},
        expected=True,
        msg="$not([null]) should return true",
    ),
    ExpressionTestCase(
        "not_null_literal_remove",
        expression={"$not": ["$$REMOVE"]},
        expected=True,
        msg="$not([$$REMOVE]) should return true, missing is falsy",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_LITERAL_TESTS))
def test_not_null_literal(collection, test):
    """Test $not with null and falsy literals."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


INSERT_TESTS = [
    ExpressionTestCase(
        "not_null_field_value",
        expression={"$not": ["$a"]},
        doc={"a": None},
        expected=True,
        msg="$not([$a]) should return true when a=null",
    ),
    ExpressionTestCase(
        "not_null_missing_field",
        expression={"$not": ["$a"]},
        doc={"_id": 1},
        expected=True,
        msg="$not([$a]) should return true when a is missing",
    ),
    ExpressionTestCase(
        "not_null_intermediate_path",
        expression={"$not": ["$a.b"]},
        doc={"a": None},
        expected=True,
        msg="$not([$a.b]) should return true when a=null",
    ),
    ExpressionTestCase(
        "not_null_leaf",
        expression={"$not": ["$a.b"]},
        doc={"a": {"b": None}},
        expected=True,
        msg="$not([$a.b]) should return true when a.b=null",
    ),
    ExpressionTestCase(
        "not_null_ifnull_to_false",
        expression={"$not": [{"$ifNull": ["$a", False]}]},
        doc={"a": None},
        expected=True,
        msg="$not([$ifNull]) should return true, null replaced with false",
    ),
    ExpressionTestCase(
        "not_null_ifnull_to_true",
        expression={"$not": [{"$ifNull": ["$a", True]}]},
        doc={"a": None},
        expected=False,
        msg="$not([$ifNull]) should return false, null replaced with true",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_not_null_missing_with_doc(collection, test):
    """Test $not with null and missing fields from documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
