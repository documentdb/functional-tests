"""Tests for $and null and missing field handling."""

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
        "null_null",
        expression={"$and": [None, None]},
        expected=False,
        msg="Should return false for null, null",
    ),
    ExpressionTestCase(
        "null_true",
        expression={"$and": [True, None]},
        expected=False,
        msg="Should return false for true, null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_LITERAL_TESTS))
def test_and_null_literal(collection, test):
    """Test $and with null literals."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MISSING_FIELD_TESTS = [
    ExpressionTestCase(
        "missing_with_truthy",
        expression={"$and": ["$a", "$nonexistent"]},
        doc={"a": True},
        expected=False,
        msg="Missing field is falsy",
    ),
    ExpressionTestCase(
        "single_missing",
        expression={"$and": ["$nonexistent"]},
        doc={},
        expected=False,
        msg="Single missing field is falsy",
    ),
]

NULL_FIELD_TESTS = [
    ExpressionTestCase(
        "null_valued",
        expression={"$and": ["$a"]},
        doc={"a": None},
        expected=False,
        msg="Should return false for null-valued field",
    ),
]

NULL_PATH_TESTS = [
    ExpressionTestCase(
        "null_intermediate",
        expression={"$and": ["$a.b"]},
        doc={"a": None},
        expected=False,
        msg="Should return false for null intermediate path",
    ),
    ExpressionTestCase(
        "null_leaf",
        expression={"$and": ["$a.b"]},
        doc={"a": {"b": None}},
        expected=False,
        msg="Should return false for null leaf in nested path",
    ),
]

INSERT_TESTS = MISSING_FIELD_TESTS + NULL_FIELD_TESTS + NULL_PATH_TESTS


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_and_null_missing_with_doc(collection, test):
    """Test $and with null and missing fields."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
