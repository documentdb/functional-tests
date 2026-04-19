"""
Tests for $cmp expression type smoke tests.

Covers literal, field path, expression operator, and array/object expression inputs.
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
        "literal_lt",
        expression={"$cmp": [5, 10]},
        expected=-1,
        msg="Literal 5 < 10",
    ),
    ExpressionTestCase(
        "literal_gt",
        expression={"$cmp": [10, 5]},
        expected=1,
        msg="Literal 10 > 5",
    ),
    ExpressionTestCase(
        "literal_eq",
        expression={"$cmp": [7, 7]},
        expected=0,
        msg="Literal 7 == 7",
    ),
    ExpressionTestCase(
        "literal_nested_expr",
        expression={"$cmp": [{"$add": [1, 2]}, 4]},
        expected=-1,
        msg="Literal $add(1,2)=3 < 4",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_cmp_expression_literal(collection, test):
    """Test $cmp with literal expression inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_path",
        expression={"$cmp": ["$a", "$b"]},
        doc={"a": 10, "b": 5},
        expected=1,
        msg="Field path $a(10) > $b(5)",
    ),
    ExpressionTestCase(
        "expression_operator",
        expression={"$cmp": [{"$abs": "$x"}, 3]},
        doc={"x": -5},
        expected=1,
        msg="abs(-5)=5 > 3",
    ),
    ExpressionTestCase(
        "array_expression",
        expression={"$cmp": [["$x", "$y"], [1, 2]]},
        doc={"x": 1, "y": 2},
        expected=0,
        msg="Array expression [1,2] == [1,2]",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_cmp_expression_with_insert(collection, test):
    """Test $cmp with field path and expression inputs."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
