"""
Tests for $gte expression type smoke tests.

Covers literal, field reference, expression operator, array expression,
object expression, composite array, and basic behavior with documents.
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
        "literal_true", expression={"$gte": [5, 3]}, expected=True, msg="Literal 5 >= 3"
    ),
    ExpressionTestCase(
        "literal_equal", expression={"$gte": [5, 5]}, expected=True, msg="Literal 5 >= 5"
    ),
    ExpressionTestCase(
        "literal_false",
        expression={"$gte": ["hello", "world"]},
        expected=False,
        msg="hello not >= world",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_gte_expression_types_literal(collection, test):
    """Test $gte with literal expression inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_REFERENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_true",
        expression={"$gte": ["$a", "$b"]},
        doc={"a": 10, "b": 5},
        expected=True,
        msg="Field a >= field b",
    ),
    ExpressionTestCase(
        "field_ref_equal",
        expression={"$gte": ["$a", "$b"]},
        doc={"a": 5, "b": 5},
        expected=True,
        msg="Field a >= field b (equal)",
    ),
    ExpressionTestCase(
        "field_ref_false",
        expression={"$gte": ["$a", "$b"]},
        doc={"a": 5, "b": 10},
        expected=False,
        msg="Field a not >= field b",
    ),
    ExpressionTestCase(
        "field_ref_string",
        expression={"$gte": ["$x", "ABC"]},
        doc={"x": "abc"},
        expected=True,
        msg="Field path 'abc' >= 'ABC'",
    ),
]

EXPRESSION_OPERATOR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expr_operator",
        expression={"$gte": [{"$abs": "$a"}, "$b"]},
        doc={"a": -5, "b": 3},
        expected=True,
        msg="abs(-5)=5 >= 3",
    ),
    ExpressionTestCase(
        "expr_add",
        expression={"$gte": [{"$add": ["$a", "$b"]}, "$c"]},
        doc={"a": 3, "b": 4, "c": 6},
        expected=True,
        msg="add(3,4)=7 >= 6",
    ),
    ExpressionTestCase(
        "expr_subtract",
        expression={"$gte": [{"$subtract": ["$a", "$b"]}, "$c"]},
        doc={"a": 10, "b": 3, "c": 6},
        expected=True,
        msg="subtract(10,3)=7 >= 6",
    ),
]

ARRAY_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expr",
        expression={"$gte": ["$a", [1, 2]]},
        doc={"a": [1, 2]},
        expected=True,
        msg="Array expression [1,2] >= [1,2] (equal)",
    ),
]

OBJECT_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "object_expr",
        expression={"$gte": ["$a", {"x": 1}]},
        doc={"a": {"x": 1}},
        expected=True,
        msg="Object expression {x:1} >= {x:1} (equal)",
    ),
]

COMPOSITE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array",
        expression={"$gte": ["$a.b", [1]]},
        doc={"a": [{"b": 1}, {"b": 2}]},
        expected=True,
        msg="Composite array $a.b [1,2] >= [1]",
    ),
    ExpressionTestCase(
        "composite_missing_path",
        expression={"$gte": ["$a.b.c.x", None]},
        doc={"a": {"b": {"c": {"d": 1}}}},
        expected=False,
        msg="Missing composite path not >= null",
    ),
]

ALL_INSERT_TESTS = (
    FIELD_REFERENCE_TESTS
    + EXPRESSION_OPERATOR_TESTS
    + ARRAY_EXPRESSION_TESTS
    + OBJECT_EXPRESSION_TESTS
    + COMPOSITE_ARRAY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_gte_expression_types_insert(collection, test):
    """Test $gte with field reference and expression inputs requiring documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
