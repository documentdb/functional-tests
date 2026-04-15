"""Tests for $or null and missing field handling."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)

NULL_LITERAL_TESTS = [
    ExpressionTestCase(
        "null_null",
        expression={"$or": [None, None]},
        expected=False,
        msg="Should return false for null, null",
    ),
    ExpressionTestCase(
        "null_false",
        expression={"$or": [None, False]},
        expected=False,
        msg="Should return false for null, false",
    ),
    ExpressionTestCase(
        "null_true",
        expression={"$or": [None, True]},
        expected=True,
        msg="Should return true for null, true",
    ),
]


@pytest.mark.parametrize("test", NULL_LITERAL_TESTS, ids=lambda t: t.id)
def test_or_null_literal(collection, test):
    """Test $or with null literals."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MISSING_FIELD_TESTS = [
    ExpressionTestCase(
        "missing_and_truthy",
        expression={"$or": ["$b", "$a"]},
        doc={"a": 1},
        expected=True,
        msg="Should return true when one field is truthy",
    ),
    ExpressionTestCase(
        "two_missing",
        expression={"$or": ["$b", "$c"]},
        doc={"a": 1},
        expected=False,
        msg="Should return false for two missing fields",
    ),
]

NULL_FIELD_TESTS = [
    ExpressionTestCase(
        "null_valued",
        expression={"$or": ["$a"]},
        doc={"a": None},
        expected=False,
        msg="Should return false for null-valued field",
    ),
]

NULL_PATH_TESTS = [
    ExpressionTestCase(
        "null_intermediate",
        expression={"$or": ["$a.b"]},
        doc={"a": None},
        expected=False,
        msg="Should return false for null intermediate path",
    ),
    ExpressionTestCase(
        "null_leaf",
        expression={"$or": ["$a.b"]},
        doc={"a": {"b": None}},
        expected=False,
        msg="Should return false for null leaf in nested path",
    ),
]

INSERT_TESTS = MISSING_FIELD_TESTS + NULL_FIELD_TESTS + NULL_PATH_TESTS


@pytest.mark.parametrize("test", INSERT_TESTS, ids=lambda t: t.id)
def test_or_null_missing_with_doc(collection, test):
    """Test $or with null and missing fields."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
