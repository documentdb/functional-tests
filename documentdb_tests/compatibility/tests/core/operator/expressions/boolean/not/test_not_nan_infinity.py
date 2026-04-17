"""Tests for $not with NaN, Infinity, and negative zero handling."""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS = [
    ExpressionTestCase(
        "not_nan_float_nan",
        expression={"$not": [float("nan")]},
        expected=False,
        msg="$not([NaN]) should return false, NaN is truthy",
    ),
    ExpressionTestCase(
        "not_nan_decimal_nan",
        expression={"$not": [Decimal128("NaN")]},
        expected=False,
        msg="$not([Decimal128 NaN]) should return false",
    ),
    ExpressionTestCase(
        "not_nan_pos_inf",
        expression={"$not": [float("inf")]},
        expected=False,
        msg="$not([Infinity]) should return false",
    ),
    ExpressionTestCase(
        "not_nan_neg_inf",
        expression={"$not": [float("-inf")]},
        expected=False,
        msg="$not([-Infinity]) should return false",
    ),
    ExpressionTestCase(
        "not_nan_double_neg_zero",
        expression={"$not": [-0.0]},
        expected=True,
        msg="$not([-0.0]) should return true, -0.0 is falsy",
    ),
    ExpressionTestCase(
        "not_nan_decimal_neg_zero",
        expression={"$not": [Decimal128("-0")]},
        expected=True,
        msg="$not([Decimal128 -0]) should return true",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_not_nan_inf_literal(collection, test):
    """Test $not with NaN, Infinity, and negative zero literals."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


INSERT_TESTS = [
    ExpressionTestCase(
        "not_nan_field_float_nan",
        expression={"$not": ["$a"]},
        doc={"a": float("nan")},
        expected=False,
        msg="$not([$a]) should return false when a=NaN",
    ),
    ExpressionTestCase(
        "not_nan_field_pos_inf",
        expression={"$not": ["$a"]},
        doc={"a": float("inf")},
        expected=False,
        msg="$not([$a]) should return false when a=Infinity",
    ),
    ExpressionTestCase(
        "not_nan_field_double_neg_zero",
        expression={"$not": ["$a"]},
        doc={"a": -0.0},
        expected=True,
        msg="$not([$a]) should return true when a=-0.0",
    ),
    ExpressionTestCase(
        "not_nan_wrapping_gt",
        expression={"$not": [{"$gt": ["$a", 0]}]},
        doc={"a": float("nan")},
        expected=True,
        msg="$not([$gt]) should return True, NaN > 0 is false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_not_nan_inf_with_doc(collection, test):
    """Test $not with NaN, Infinity, and negative zero from field paths."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
