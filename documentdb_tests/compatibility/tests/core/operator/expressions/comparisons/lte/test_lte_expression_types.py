"""
Tests for $lte expression types, array index paths, and system variables.

Covers literal, field path, expression operator, array expression, object
expression, composite array, missing paths, and system variable inputs.
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
        "literal_int", expression={"$lte": [1, 2]}, expected=True, msg="literal 1 <= 2"
    ),
    ExpressionTestCase(
        "literal_string", expression={"$lte": ["a", "b"]}, expected=True, msg="literal 'a' <= 'b'"
    ),
    ExpressionTestCase(
        "literal_equal", expression={"$lte": [5, 5]}, expected=True, msg="literal 5 <= 5"
    ),
    ExpressionTestCase(
        "literal_false", expression={"$lte": [5, 3]}, expected=False, msg="5 not <= 3"
    ),
]

FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_path_true",
        expression={"$lte": ["$a", "$b"]},
        doc={"a": 5, "b": 10},
        expected=True,
        msg="field $a(5) <= $b(10)",
    ),
    ExpressionTestCase(
        "field_path_equal",
        expression={"$lte": ["$a", "$b"]},
        doc={"a": 5, "b": 5},
        expected=True,
        msg="field $a(5) <= $b(5) (equal)",
    ),
    ExpressionTestCase(
        "field_path_false",
        expression={"$lte": ["$a", "$b"]},
        doc={"a": 10, "b": 5},
        expected=False,
        msg="field $a(10) not <= $b(5)",
    ),
    ExpressionTestCase(
        "field_ref_string",
        expression={"$lte": ["$x", "abc"]},
        doc={"x": "ABC"},
        expected=True,
        msg="Field path 'ABC' <= 'abc'",
    ),
    ExpressionTestCase(
        "expression_operator_input",
        expression={"$lte": [{"$abs": "$a"}, "$b"]},
        doc={"a": -2, "b": 3},
        expected=True,
        msg="abs(-2)=2 <= 3",
    ),
    ExpressionTestCase(
        "system_var_current",
        expression={"$lte": ["$$CURRENT.a", 1]},
        doc={"a": 1},
        expected=True,
        msg="$$CURRENT.a equivalent to $a",
    ),
]

ARRAY_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expr",
        expression={"$lte": ["$a", [1, 2]]},
        doc={"a": [1, 2]},
        expected=True,
        msg="Array [1,2] <= [1,2] (equal)",
    ),
]

OBJECT_EXPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "object_expr",
        expression={"$lte": ["$a", {"x": 1}]},
        doc={"a": {"x": 1}},
        expected=True,
        msg="Object {x:1} <= {x:1} (equal)",
    ),
]

COMPOSITE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_missing_path",
        expression={"$lte": ["$a.b.c.x", None]},
        doc={"a": {"b": {"c": {"d": 1}}}},
        expected=True,
        msg="Missing composite path <= null",
    ),
]

ALL_LITERAL_TESTS = LITERAL_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_LITERAL_TESTS))
def test_lte_expression_types_literal(collection, test):
    """Test $lte with literal expression inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


ALL_INSERT_TESTS = (
    FIELD_PATH_TESTS + ARRAY_EXPRESSION_TESTS + OBJECT_EXPRESSION_TESTS + COMPOSITE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_lte_expression_types_insert(collection, test):
    """Test $lte with field reference and expression inputs requiring documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
