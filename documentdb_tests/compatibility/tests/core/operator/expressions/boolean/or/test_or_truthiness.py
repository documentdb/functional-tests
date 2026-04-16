"""
Tests for $or truthiness evaluation — representative types, combinations, return type.
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
        "all_falsy",
        expression={"$or": [False, 0, None]},
        expected=False,
        msg="Should return false for all falsy",
    ),
    ExpressionTestCase(
        "all_numeric_zeros",
        expression={"$or": [0, Int64(0), 0.0, Decimal128("0")]},
        expected=False,
        msg="Should return false for all numeric zeros",
    ),
    ExpressionTestCase(
        "mixed_falsy_truthy",
        expression={"$or": [False, 0, None, 1]},
        expected=True,
        msg="Should return true when one truthy value present",
    ),
]

ORDER_SENSITIVITY_TESTS = [
    ExpressionTestCase(
        "true_first",
        expression={"$or": [True, 0, None]},
        expected=True,
        msg="True at first position",
    ),
    ExpressionTestCase(
        "true_middle",
        expression={"$or": [0, True, None]},
        expected=True,
        msg="True at middle position",
    ),
    ExpressionTestCase(
        "true_last",
        expression={"$or": [0, None, True]},
        expected=True,
        msg="True at last position",
    ),
]

ALL_TESTS = COMBO_TESTS + ORDER_SENSITIVITY_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_or_truthiness(collection, test):
    """Test $or truthiness evaluation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


RETURN_TYPE_TESTS = [
    ExpressionTestCase(
        "return_type_true",
        expression={"$or": [True, False]},
        expected="bool",
        msg="Should return bool type",
    ),
    ExpressionTestCase(
        "return_type_false",
        expression={"$or": [None]},
        expected="bool",
        msg="Should return bool type for falsy",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RETURN_TYPE_TESTS))
def test_or_return_type(collection, test):
    """Test $or return type."""
    result = execute_expression(collection, {"$type": test.expression})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
