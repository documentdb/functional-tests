"""$toBool numeric truthiness tests: falsy zeros, truthy non-zeros, and special float values."""

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
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_HALF,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Numeric Truthiness - Falsy Zeros]: numeric zero values produce false regardless
# of type, sign, exponent, or trailing zeros.
TOBOOL_FALSY_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "falsy_int32_zero",
        msg="int32 zero converts to false",
        expression={"$toBool": INT32_ZERO},
        expected=False,
    ),
    ExpressionTestCase(
        "falsy_int64_zero",
        msg="int64 zero converts to false",
        expression={"$toBool": INT64_ZERO},
        expected=False,
    ),
    ExpressionTestCase(
        "falsy_double_zero",
        msg="double 0.0 converts to false",
        expression={"$toBool": DOUBLE_ZERO},
        expected=False,
    ),
    ExpressionTestCase(
        "falsy_double_negative_zero",
        msg="double -0.0 converts to false",
        expression={"$toBool": DOUBLE_NEGATIVE_ZERO},
        expected=False,
    ),
    ExpressionTestCase(
        "falsy_decimal_zero",
        msg="Decimal128 zero converts to false",
        expression={"$toBool": DECIMAL128_ZERO},
        expected=False,
    ),
    ExpressionTestCase(
        "falsy_decimal_negative_zero",
        msg="Decimal128 negative zero converts to false",
        expression={"$toBool": DECIMAL128_NEGATIVE_ZERO},
        expected=False,
    ),
    ExpressionTestCase(
        "falsy_decimal_zero_point_zero",
        msg="Decimal128 0.0 converts to false",
        expression={"$toBool": Decimal128("0.0")},
        expected=False,
    ),
    ExpressionTestCase(
        "falsy_decimal_zero_max_exponent",
        msg="Decimal128 0E+6144 converts to false",
        expression={"$toBool": Decimal128("0E+6144")},
        expected=False,
    ),
    ExpressionTestCase(
        "falsy_decimal_neg_zero_decimal",
        msg="Decimal128('-0.0') converts to false",
        expression={"$toBool": Decimal128("-0.0")},
        expected=False,
    ),
]

# Property [Numeric Truthiness - Truthy Non-Zeros]: any non-zero numeric value produces true
# regardless of type, sign, magnitude, or precision.
TOBOOL_TRUTHY_NONZERO_TESTS: list[ExpressionTestCase] = [
    # int32
    ExpressionTestCase(
        "truthy_int32_one",
        msg="int32 1 converts to true",
        expression={"$toBool": 1},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_int32_neg_one",
        msg="int32 -1 converts to true",
        expression={"$toBool": -1},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_int32_max",
        msg="INT32_MAX converts to true",
        expression={"$toBool": INT32_MAX},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_int32_min",
        msg="INT32_MIN converts to true",
        expression={"$toBool": INT32_MIN},
        expected=True,
    ),
    # int64
    ExpressionTestCase(
        "truthy_int64_one",
        msg="int64 1 converts to true",
        expression={"$toBool": Int64(1)},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_int64_neg_one",
        msg="int64 -1 converts to true",
        expression={"$toBool": Int64(-1)},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_int64_max",
        msg="INT64_MAX converts to true",
        expression={"$toBool": INT64_MAX},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_int64_min",
        msg="INT64_MIN converts to true",
        expression={"$toBool": INT64_MIN},
        expected=True,
    ),
    # double
    ExpressionTestCase(
        "truthy_double_fraction",
        msg="double 0.5 converts to true",
        expression={"$toBool": DOUBLE_HALF},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_double_subnormal",
        msg="double minimum positive subnormal converts to true",
        expression={"$toBool": DOUBLE_MIN_SUBNORMAL},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_double_near_max",
        msg="double near-max finite value converts to true",
        expression={"$toBool": DOUBLE_NEAR_MAX},
        expected=True,
    ),
    # Decimal128
    ExpressionTestCase(
        "truthy_decimal_one",
        msg="Decimal128 1 converts to true",
        expression={"$toBool": Decimal128("1")},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_decimal_many_trailing_zeros",
        msg="Decimal128 with max-precision trailing zeros converts to true",
        expression={"$toBool": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_decimal_max",
        msg="Decimal128 max value converts to true",
        expression={"$toBool": DECIMAL128_MAX},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_decimal_min",
        msg="Decimal128 min (most negative) value converts to true",
        expression={"$toBool": DECIMAL128_MIN},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_decimal_min_positive",
        msg="Decimal128 smallest positive value converts to true",
        expression={"$toBool": DECIMAL128_MIN_POSITIVE},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_decimal_max_negative",
        msg="Decimal128 largest negative (closest to zero) converts to true",
        expression={"$toBool": DECIMAL128_MAX_NEGATIVE},
        expected=True,
    ),
]

# Property [Numeric Truthiness - Special Float Values]: NaN and Infinity values of both
# double and Decimal128 produce true.
TOBOOL_SPECIAL_FLOAT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "special_double_nan",
        msg="double NaN converts to true",
        expression={"$toBool": FLOAT_NAN},
        expected=True,
    ),
    ExpressionTestCase(
        "special_decimal_nan",
        msg="Decimal128 NaN converts to true",
        expression={"$toBool": DECIMAL128_NAN},
        expected=True,
    ),
    ExpressionTestCase(
        "special_double_pos_infinity",
        msg="double +Infinity converts to true",
        expression={"$toBool": FLOAT_INFINITY},
        expected=True,
    ),
    ExpressionTestCase(
        "special_double_neg_infinity",
        msg="double -Infinity converts to true",
        expression={"$toBool": FLOAT_NEGATIVE_INFINITY},
        expected=True,
    ),
    ExpressionTestCase(
        "special_decimal_pos_infinity",
        msg="Decimal128 +Infinity converts to true",
        expression={"$toBool": DECIMAL128_INFINITY},
        expected=True,
    ),
    ExpressionTestCase(
        "special_decimal_neg_infinity",
        msg="Decimal128 -Infinity converts to true",
        expression={"$toBool": DECIMAL128_NEGATIVE_INFINITY},
        expected=True,
    ),
]

TOBOOL_NUMERIC_TESTS = (
    TOBOOL_FALSY_ZERO_TESTS + TOBOOL_TRUTHY_NONZERO_TESTS + TOBOOL_SPECIAL_FLOAT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TOBOOL_NUMERIC_TESTS))
def test_toBool_numeric(collection, test: ExpressionTestCase):
    """$toBool converts numeric inputs: zeros are falsy, non-zeros and special values are truthy."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
