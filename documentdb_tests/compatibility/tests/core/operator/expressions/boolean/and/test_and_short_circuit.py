"""Tests for $and short-circuit behavior — non-guaranteed optimization."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

CONST_OPTIMIZATION_TESTS = [
    ExpressionTestCase(
        "falsy_literal_with_error",
        expression={"$and": [False, {"$divide": [1, "$x"]}]},
        doc={"x": 0},
        expected=False,
        msg="Should return false — optimizer folds falsy literal",
    ),
    ExpressionTestCase(
        "const_0_x",
        expression={"$and": [0, "$x"]},
        doc={"x": True},
        expected=False,
        msg="Should return false when first arg is falsy literal 0",
    ),
    ExpressionTestCase(
        "const_all_const",
        expression={"$and": [1, 1, 1, 0]},
        doc={"_id": 1},
        expected=False,
        msg="Should return false for all-constant with one falsy",
    ),
]

NO_OPTIMIZATION_TESTS = [
    ExpressionTestCase(
        "no_opt_1_x_true",
        expression={"$and": [1, "$x"]},
        doc={"x": True},
        expected=True,
        msg="Should return true when field ref is truthy",
    ),
    ExpressionTestCase(
        "no_opt_1_x_false",
        expression={"$and": [1, "$x"]},
        doc={"x": False},
        expected=False,
        msg="Should return false when field ref is falsy",
    ),
]

ERROR_TESTS = [
    ExpressionTestCase(
        "all_expressions_error",
        expression={"$and": [{"$divide": [1, "$x"]}, {"$divide": [1, "$y"]}]},
        doc={"x": 0, "y": 0},
        error_code=BAD_VALUE_ERROR,
        msg="Should error when all expressions cause division by zero",
    ),
]

ALL_TESTS = CONST_OPTIMIZATION_TESTS + NO_OPTIMIZATION_TESTS + ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_and_short_circuit(collection, test):
    """Test $and short-circuit behavior."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
