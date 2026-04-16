"""
Tests for $and truthiness evaluation — representative types, combinations, return type.
A comprehensive Truthy/Falsy test is located at test_expressions_boolean_coercion.py
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

COMBO_TESTS = [
    ExpressionTestCase(
        "all_truthy",
        expression={"$and": [True, 1, "hello"]},
        expected=True,
        msg="Should return true for all truthy",
    ),
    ExpressionTestCase(
        "all_numeric_zeros",
        expression={"$and": [0, Int64(0), 0.0, Decimal128("0")]},
        expected=False,
        msg="Should return false for all numeric zeros",
    ),
    ExpressionTestCase(
        "mixed_truthy_falsy",
        expression={"$and": [True, 1, "hello", 0]},
        expected=False,
        msg="Should return false when one falsy value present",
    ),
]

ORDER_SENSITIVITY_TESTS = [
    ExpressionTestCase(
        "false_first",
        expression={"$and": [False, 1, "hello"]},
        expected=False,
        msg="False at first position",
    ),
    ExpressionTestCase(
        "false_middle",
        expression={"$and": [1, False, "hello"]},
        expected=False,
        msg="False at middle position",
    ),
    ExpressionTestCase(
        "false_last",
        expression={"$and": [1, "hello", False]},
        expected=False,
        msg="False at last position",
    ),
]

ALL_TESTS = COMBO_TESTS + ORDER_SENSITIVITY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_and_truthiness(collection, test):
    """Test $and truthiness evaluation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


RETURN_TYPE_TESTS = [
    ExpressionTestCase(
        "return_type_true",
        expression={"$and": [True, True]},
        expected="bool",
        msg="Should return bool type",
    ),
    ExpressionTestCase(
        "return_type_false",
        expression={"$and": [None]},
        expected="bool",
        msg="Should return bool type for falsy",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RETURN_TYPE_TESTS))
def test_and_return_type(collection, test):
    """Test $and return type."""
    result = execute_expression(collection, {"$type": test.expression})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
