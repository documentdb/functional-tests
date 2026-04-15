"""
Null and missing field handling tests for $let.

Covers null propagation, missing field behavior, field lookup in variable
assignments, and $let across multiple documents.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess

NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_in_arithmetic",
        expression={"$let": {"vars": {"x": None}, "in": {"$add": ["$$x", 1]}}},
        expected=None,
        msg="Null propagation: null + 1 = null",
    ),
]


@pytest.mark.parametrize("test", NULL_TESTS, ids=lambda t: t.id)
def test_let_null_propagation(collection, test):
    """Test $let null propagation through variables."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_LOOKUP_SUCCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        expression={"$let": {"vars": {"x": "$a.b"}, "in": "$$x"}},
        doc={"a": {"b": 99}},
        expected=99,
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        "composite_array_path",
        expression={"$let": {"vars": {"x": "$a.b"}, "in": "$$x"}},
        doc={"a": [{"b": 10}, {"b": 20}]},
        expected=[10, 20],
        msg="Should resolve composite array path",
    ),
]


@pytest.mark.parametrize("test", FIELD_LOOKUP_SUCCESS_TESTS, ids=lambda t: t.id)
def test_let_field_lookup(collection, test):
    """Test $let with field path variable assignments."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_LOOKUP_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_field",
        expression={"$let": {"vars": {"x": "$nonexistent"}, "in": "$$x"}},
        doc={"a": 1},
        msg="Missing field variable should omit result",
    ),
]


@pytest.mark.parametrize("test", FIELD_LOOKUP_MISSING_TESTS, ids=lambda t: t.id)
def test_let_field_lookup_missing(collection, test):
    """Test $let with missing field path variable assignments."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertSuccess(result, [{}], msg=test.msg)
