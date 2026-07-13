"""$toDecimal double conversion tests: 15 significant digits, zero, NaN, and infinity."""

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
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_TWO_AND_HALF,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Double Conversion]: non-zero finite doubles produce exactly 15 significant digits;
# zero, negative zero, NaN, and infinity have special mappings.
TODECIMAL_DOUBLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_two_point_five",
        msg="2.5 converts with 15 significant digits",
        expression={"$toDecimal": DOUBLE_TWO_AND_HALF},
        expected=Decimal128("2.50000000000000"),
    ),
    ExpressionTestCase(
        "double_negative",
        msg="Negative double converts with 15 significant digits",
        expression={"$toDecimal": -DOUBLE_TWO_AND_HALF},
        expected=Decimal128("-2.50000000000000"),
    ),
    ExpressionTestCase(
        "double_zero",
        msg="0.0 converts to Decimal128('0') with no trailing zeros",
        expression={"$toDecimal": DOUBLE_ZERO},
        expected=DECIMAL128_ZERO,
    ),
    ExpressionTestCase(
        "double_negative_zero",
        msg="Negative zero double preserves sign",
        expression={"$toDecimal": DOUBLE_NEGATIVE_ZERO},
        expected=DECIMAL128_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "double_nan",
        msg="double NaN converts to Decimal128 NaN",
        expression={"$toDecimal": FLOAT_NAN},
        expected=DECIMAL128_NAN,
    ),
    ExpressionTestCase(
        "double_pos_inf",
        msg="double Infinity converts to Decimal128 Infinity",
        expression={"$toDecimal": FLOAT_INFINITY},
        expected=DECIMAL128_INFINITY,
    ),
    ExpressionTestCase(
        "double_neg_inf",
        msg="double -Infinity converts to Decimal128 -Infinity",
        expression={"$toDecimal": FLOAT_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "double_round_up_power_of_10",
        msg="Double rounds up to next power of 10 at 15th digit boundary",
        expression={"$toDecimal": 9.999999999999998e15},
        expected=Decimal128("1.00000000000000E+16"),
    ),
    ExpressionTestCase(
        "double_round_up",
        msg="Double rounds up at 15th significant digit",
        expression={"$toDecimal": 1.234567890123456},
        expected=Decimal128("1.23456789012346"),
    ),
    ExpressionTestCase(
        "double_round_misleading_literal",
        msg="Double rounds based on stored imprecise value, not source literal",
        expression={"$toDecimal": 1.234567890123455},
        expected=Decimal128("1.23456789012345"),
    ),
    ExpressionTestCase(
        "double_round_down",
        msg="Double rounds down at 15th significant digit",
        expression={"$toDecimal": 1.234567890123451},
        expected=Decimal128("1.23456789012345"),
    ),
    ExpressionTestCase(
        "double_round_to_one",
        msg="Double 0.9999999999999996 rounds to 1.00000000000000",
        expression={"$toDecimal": 0.9999999999999996},
        expected=Decimal128("1.00000000000000"),
    ),
    ExpressionTestCase(
        "double_max_safe_int",
        msg="Max safe integer (2^53) converts with 15 significant digits",
        expression={"$toDecimal": float(2**53)},
        expected=Decimal128("9.00719925474099E+15"),
    ),
    ExpressionTestCase(
        "double_subnormal",
        msg="Minimum positive subnormal double converts with 15 significant digits",
        expression={"$toDecimal": DOUBLE_MIN_SUBNORMAL},
        expected=Decimal128("4.94065645841247E-324"),
    ),
    ExpressionTestCase(
        "double_negative_subnormal",
        msg="Minimum negative subnormal double converts with 15 significant digits",
        expression={"$toDecimal": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected=Decimal128("-4.94065645841247E-324"),
    ),
    ExpressionTestCase(
        "double_near_max",
        msg="Near-max double converts with 15 significant digits",
        expression={"$toDecimal": DOUBLE_MAX},
        expected=Decimal128("1.79769313486232E+308"),
    ),
    ExpressionTestCase(
        "double_near_min",
        msg="Near-min double converts with 15 significant digits",
        expression={"$toDecimal": DOUBLE_MIN},
        expected=Decimal128("-1.79769313486232E+308"),
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_DOUBLE_TESTS))
def test_toDecimal_double(collection, test: ExpressionTestCase):
    """$toDecimal converts double inputs to Decimal128 with 15 significant digits."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
