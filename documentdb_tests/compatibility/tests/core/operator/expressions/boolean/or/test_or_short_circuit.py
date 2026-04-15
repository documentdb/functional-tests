"""Tests for $or short-circuit behavior — non-guaranteed optimization."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR

CONST_OPTIMIZATION_TESTS = [
    ExpressionTestCase(
        "truthy_literal_with_error",
        expression={"$or": [{"$divide": [1, "$x"]}, True]},
        doc={"x": 0},
        expected=True,
        msg="Should return true — optimizer folds truthy literal",
    ),
    ExpressionTestCase(
        "const_1_x",
        expression={"$or": [1, "$x"]},
        doc={"x": False},
        expected=True,
        msg="Should return true when first arg is truthy literal 1",
    ),
    ExpressionTestCase(
        "const_all_const",
        expression={"$or": [0, 0, 0, 1]},
        doc={"_id": 1},
        expected=True,
        msg="Should return true for all-constant with one truthy",
    ),
]

NO_OPTIMIZATION_TESTS = [
    ExpressionTestCase(
        "no_opt_0_x_true",
        expression={"$or": [0, "$x"]},
        doc={"x": True},
        expected=True,
        msg="Should return true when field ref is truthy",
    ),
    ExpressionTestCase(
        "no_opt_0_x_false",
        expression={"$or": [0, "$x"]},
        doc={"x": False},
        expected=False,
        msg="Should return false when all are falsy",
    ),
]

ERROR_TESTS = [
    ExpressionTestCase(
        "all_expressions_error",
        expression={"$or": [{"$divide": [1, "$x"]}, {"$divide": [1, "$y"]}]},
        doc={"x": 0, "y": 0},
        error_code=BAD_VALUE_ERROR,
        msg="Should error when all expressions cause division by zero",
    ),
]

ALL_TESTS = CONST_OPTIMIZATION_TESTS + NO_OPTIMIZATION_TESTS + ERROR_TESTS


@pytest.mark.parametrize("test", ALL_TESTS, ids=lambda t: t.id)
def test_or_short_circuit(collection, test):
    """Test $or short-circuit behavior."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
