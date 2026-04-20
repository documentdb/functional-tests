"""
Tests for $lt expression type smoke tests.

Covers literal, field reference, expression operator, array expression,
and object expression.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_true", expression={"$lt": [3, 5]}, expected=True, msg="Literal 3 < 5"
    ),
    ExpressionTestCase(
        "literal_false", expression={"$lt": [5, 3]}, expected=False, msg="5 not < 3"
    ),
    ExpressionTestCase(
        "literal_equal", expression={"$lt": [5, 5]}, expected=False, msg="5 not < 5"
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_lt_expression_types_literal(collection, test):
    """Test $lt with literal expression inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_REFERENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_true",
        expression={"$lt": ["$a", "$b"]},
        doc={"a": 5, "b": 10},
        expected=True,
        msg="Field a < field b",
    ),
    ExpressionTestCase(
        "field_ref_false",
        expression={"$lt": ["$a", "$b"]},
        doc={"a": 10, "b": 5},
        expected=False,
        msg="Field a not < field b",
    ),
    ExpressionTestCase(
        "field_ref_string",
        expression={"$lt": ["$x", "abc"]},
        doc={"x": "ABC"},
        expected=True,
        msg="Field path 'ABC' < 'abc'",
    ),
]

EXPRESSION_OPERATOR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expr_operator",
        expression={"$lt": [{"$abs": "$a"}, 10]},
        doc={"a": -5},
        expected=True,
        msg="abs(-5)=5 < 10",
    ),
    ExpressionTestCase(
        "system_var_current",
        expression={"$lt": ["$$CURRENT.a", 2]},
        doc={"a": 1},
        expected=True,
        msg="$$CURRENT.a equivalent to $a",
    ),
]

COMPOSITE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_missing_path",
        expression={"$lt": ["$a.b.c.x", None]},
        doc={"a": {"b": {"c": {"d": 1}}}},
        expected=True,
        msg="Missing composite path < null",
    ),
]

ARRAY_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expr",
        expression={"$lt": ["$a", [1, 2]]},
        doc={"a": [1, 1]},
        expected=True,
        msg="Array [1,1] < [1,2]",
    ),
]

OBJECT_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "object_expr",
        expression={"$lt": ["$a", {"x": 2}]},
        doc={"a": {"x": 1}},
        expected=True,
        msg="Object {x:1} < {x:2}",
    ),
]
ALL_INSERT_TESTS = (
    FIELD_REFERENCE_TESTS
    + EXPRESSION_OPERATOR_TESTS
    + ARRAY_EXPRESSION_TESTS
    + OBJECT_EXPRESSION_TESTS
    + COMPOSITE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_lt_expression_types_insert(collection, test):
    """Test $lt with field reference and expression inputs requiring documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
