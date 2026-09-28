"""
Null, missing, and Infinity tests for $pow expression.

Covers null/missing short-circuiting for the base and exponent, plus every
combination of NaN, Infinity, and -Infinity as the base and/or exponent for
double and Decimal128.
"""

import math

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    MISSING,
)

POW_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_exponent",
        expression={"$pow": [2, None]},
        expected=None,
        msg="Should return null for null exponent",
    ),
    ExpressionTestCase(
        "null_base",
        expression={"$pow": [None, 2]},
        expected=None,
        msg="Should return null for null base",
    ),
    ExpressionTestCase(
        "missing_base",
        expression={"$pow": [MISSING, 2]},
        expected=None,
        msg="Should return null for missing base",
    ),
    ExpressionTestCase(
        "missing_exponent",
        expression={"$pow": [2, MISSING]},
        expected=None,
        msg="Should return null for missing exponent",
    ),
    ExpressionTestCase(
        "both_null",
        expression={"$pow": [None, None]},
        expected=None,
        msg="Should return null for both null",
    ),
    ExpressionTestCase(
        "infinity_base",
        expression={"$pow": [FLOAT_INFINITY, 2]},
        expected=float("inf"),
        msg="Should handle infinity base",
    ),
    ExpressionTestCase(
        "infinity_exponent",
        expression={"$pow": [2, FLOAT_INFINITY]},
        expected=float("inf"),
        msg="Should handle infinity exponent",
    ),
    ExpressionTestCase(
        "infinity_to_zero",
        expression={"$pow": [FLOAT_INFINITY, 0]},
        expected=1.0,
        msg="Should handle infinity to zero",
    ),
    ExpressionTestCase(
        "infinity_negative_exp",
        expression={"$pow": [FLOAT_INFINITY, -1]},
        expected=0.0,
        msg="Should handle infinity negative exp",
    ),
    ExpressionTestCase(
        "fractional_base_infinity_exponent",
        expression={"$pow": [0.5, FLOAT_INFINITY]},
        expected=0.0,
        msg="Should handle base in (0,1) raised to +infinity",
    ),
    ExpressionTestCase(
        "base_gt_one_negative_infinity_exponent",
        expression={"$pow": [2, FLOAT_NEGATIVE_INFINITY]},
        expected=0.0,
        msg="Should handle base greater than one raised to -infinity",
    ),
    ExpressionTestCase(
        "one_base_infinity_exponent",
        expression={"$pow": [1, FLOAT_INFINITY]},
        expected=1.0,
        msg="Should handle base of one raised to +infinity",
    ),
    ExpressionTestCase(
        "decimal_infinity_base",
        expression={"$pow": [DECIMAL128_INFINITY, 2]},
        expected=Decimal128("Infinity"),
        msg="Should handle decimal infinity base",
    ),
    ExpressionTestCase(
        "decimal_neg_infinity_odd",
        expression={"$pow": [DECIMAL128_NEGATIVE_INFINITY, 3]},
        expected=Decimal128("-Infinity"),
        msg="Should handle decimal neg infinity odd",
    ),
    ExpressionTestCase(
        "decimal_neg_infinity_even",
        expression={"$pow": [DECIMAL128_NEGATIVE_INFINITY, 2]},
        expected=Decimal128("Infinity"),
        msg="Should handle decimal neg infinity even",
    ),
    ExpressionTestCase(
        "neg_inf_negative_exp",
        expression={"$pow": [FLOAT_NEGATIVE_INFINITY, -1]},
        expected=-0.0,
        msg="Should handle neg inf negative exp",
    ),
    ExpressionTestCase(
        "neg_inf_fractional_exp",
        expression={"$pow": [FLOAT_NEGATIVE_INFINITY, 0.5]},
        expected=float("inf"),
        msg="Should handle neg inf fractional exp",
    ),
    ExpressionTestCase(
        "decimal_neg_inf_negative_exp",
        expression={"$pow": [DECIMAL128_NEGATIVE_INFINITY, -1]},
        expected=Decimal128("0E-6176"),
        msg="Should handle decimal neg inf negative exp",
    ),
    ExpressionTestCase(
        "nan_base",
        expression={"$pow": [FLOAT_NAN, 2]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan base",
    ),
    ExpressionTestCase(
        "nan_exponent",
        expression={"$pow": [2, FLOAT_NAN]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for nan exponent",
    ),
    ExpressionTestCase(
        "both_nan",
        expression={"$pow": [FLOAT_NAN, FLOAT_NAN]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for both nan",
    ),
    ExpressionTestCase(
        "negative_fractional_exp",
        expression={"$pow": [-1, 0.5]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should handle negative fractional exp",
    ),
    ExpressionTestCase(
        "negative_base_fractional_exp",
        expression={"$pow": [-2, 2.5]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should handle negative base fractional exp",
    ),
    ExpressionTestCase(
        "decimal_nan_base",
        expression={"$pow": [DECIMAL128_NAN, 2]},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal nan base",
    ),
    ExpressionTestCase(
        "decimal_nan_exponent",
        expression={"$pow": [2, DECIMAL128_NAN]},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal nan exponent",
    ),
    ExpressionTestCase(
        "decimal_both_nan",
        expression={"$pow": [DECIMAL128_NAN, DECIMAL128_NAN]},
        expected=DECIMAL128_NAN,
        msg="Should return NaN for decimal both nan",
    ),
    ExpressionTestCase(
        "double_negative_zero_base_odd_exp",
        expression={"$pow": [DOUBLE_NEGATIVE_ZERO, 3]},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="Should preserve negative-zero sign for odd exponent",
    ),
    ExpressionTestCase(
        "double_negative_zero_base_even_exp",
        expression={"$pow": [DOUBLE_NEGATIVE_ZERO, 4]},
        expected=0.0,
        msg="Should return positive zero for even exponent",
    ),
    ExpressionTestCase(
        "decimal_negative_zero_base_odd_exp",
        expression={"$pow": [DECIMAL128_NEGATIVE_ZERO, 3]},
        expected=Decimal128("0E-6176"),
        msg="Should not preserve negative-zero sign for decimal128 (unlike double)",
    ),
    ExpressionTestCase(
        "decimal_negative_zero_base_even_exp",
        expression={"$pow": [DECIMAL128_NEGATIVE_ZERO, 4]},
        expected=Decimal128("0E-6176"),
        msg="Should return zero for decimal128 negative-zero base, even exponent",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POW_LITERAL_TESTS))
def test_pow_literal(collection, test):
    """Test $pow from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
