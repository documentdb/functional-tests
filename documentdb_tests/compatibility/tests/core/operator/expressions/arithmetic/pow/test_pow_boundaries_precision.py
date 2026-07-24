"""
Boundary and precision tests for $pow expression.

Covers INT32/INT64 max/min (and adjacent) values through the promotion
chain, double overflow/underflow near the double range limits (including
subnormals), and Decimal128 precision/boundary values, plus rounding
near half values for double and Decimal128.
"""

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_HALF,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ONE_AND_HALF,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

POW_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ten_to_ten",
        expression={"$pow": [10, 10]},
        expected=Int64(10000000000),
        msg="Should return correct result for ten to ten",
    ),
    ExpressionTestCase(
        "two_to_twenty",
        expression={"$pow": [2, 20]},
        expected=1048576,
        msg="Should return correct result for two to twenty",
    ),
    ExpressionTestCase(
        "two_to_thirty",
        expression={"$pow": [2, 30]},
        expected=1073741824,
        msg="Should return correct result for two to thirty",
    ),
    ExpressionTestCase(
        "int32_max_base",
        expression={"$pow": [INT32_MAX, 1]},
        expected=INT32_MAX,
        msg="Should handle int32 max base",
    ),
    ExpressionTestCase(
        "int32_max_minus_1_base",
        expression={"$pow": [INT32_MAX_MINUS_1, 1]},
        expected=INT32_MAX_MINUS_1,
        msg="Should handle int32 max minus 1 base",
    ),
    ExpressionTestCase(
        "int32_max_squared",
        expression={"$pow": [INT32_MAX, 2]},
        expected=pytest.approx(4.611686014132421e18),
        msg="Should handle int32 max squared",
    ),
    ExpressionTestCase(
        "int64_max_base",
        expression={"$pow": [INT64_MAX, 1]},
        expected=INT64_MAX,
        msg="Should handle int64 max base",
    ),
    ExpressionTestCase(
        "int64_max_minus_1_base",
        expression={"$pow": [INT64_MAX_MINUS_1, 1]},
        expected=INT64_MAX_MINUS_1,
        msg="Should handle int64 max minus 1 base",
    ),
    ExpressionTestCase(
        "int32_min_base_even",
        expression={"$pow": [INT32_MIN, 2]},
        expected=pytest.approx(4.611686018427388e18),
        msg="Should handle int32 min base even",
    ),
    ExpressionTestCase(
        "int32_min_plus_1_base_even",
        expression={"$pow": [INT32_MIN_PLUS_1, 2]},
        expected=pytest.approx(4.611686014132421e18),
        msg="Should handle int32 min plus 1 base even",
    ),
    ExpressionTestCase(
        "int64_min_base_even",
        expression={"$pow": [INT64_MIN, 2]},
        expected=pytest.approx(8.507059173023462e37),
        msg="Should handle int64 min base even",
    ),
    ExpressionTestCase(
        "int64_min_plus_1_base_even",
        expression={"$pow": [INT64_MIN_PLUS_1, 2]},
        expected=pytest.approx(8.507059173023462e37),
        msg="Should handle int64 min plus 1 base even",
    ),
    ExpressionTestCase(
        "near_overflow",
        expression={"$pow": [10, 308]},
        expected=pytest.approx(1e308),
        msg="Should handle near overflow",
    ),
    ExpressionTestCase(
        "overflow",
        expression={"$pow": [10, 309]},
        expected=float("inf"),
        msg="Should handle overflow",
    ),
    ExpressionTestCase(
        "overflow_two",
        expression={"$pow": [2, 1024]},
        expected=float("inf"),
        msg="Should handle overflow two",
    ),
    ExpressionTestCase(
        "extreme_overflow",
        expression={"$pow": [1000, 1000]},
        expected=float("inf"),
        msg="Should handle extreme overflow",
    ),
    ExpressionTestCase(
        "tiny_exponent",
        expression={"$pow": [2, 0.0001]},
        expected=pytest.approx(1.0000693387462580),
        msg="Should return correct result for tiny exponent",
    ),
    ExpressionTestCase(
        "tiny_exponent_ten",
        expression={"$pow": [10, 0.001]},
        expected=pytest.approx(1.0023052380778994),
        msg="Should return correct result for tiny exponent ten",
    ),
    ExpressionTestCase(
        "double_min_subnormal_base",
        expression={"$pow": [DOUBLE_MIN_SUBNORMAL, 2]},
        expected=0.0,
        msg="Should underflow to zero for min subnormal double base squared",
    ),
    ExpressionTestCase(
        "double_min_negative_subnormal_base",
        expression={"$pow": [DOUBLE_MIN_NEGATIVE_SUBNORMAL, 3]},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="Should underflow to negative zero for min negative subnormal double cubed",
    ),
    ExpressionTestCase(
        "double_near_max_base",
        expression={"$pow": [DOUBLE_NEAR_MAX, 1]},
        expected=DOUBLE_NEAR_MAX,
        msg="Should preserve near-max double value when raised to the first power",
    ),
    ExpressionTestCase(
        "double_near_min_base",
        expression={"$pow": [DOUBLE_NEAR_MIN, 1]},
        expected=DOUBLE_NEAR_MIN,
        msg="Should preserve near-min double value when raised to the first power",
    ),
    ExpressionTestCase(
        "decimal_max_base_to_one",
        expression={"$pow": [DECIMAL128_MAX, 1]},
        expected=DECIMAL128_INFINITY,
        msg=(
            "$pow overflows Decimal128 max to infinity even at exponent 1 "
            "(unlike $multiply, which preserves the value)"
        ),
    ),
    ExpressionTestCase(
        "decimal_min_base_to_one",
        expression={"$pow": [DECIMAL128_MIN, 1]},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$pow overflows Decimal128 min to negative infinity even at exponent 1",
    ),
    ExpressionTestCase(
        "decimal_max_base_squared",
        expression={"$pow": [DECIMAL128_MAX, 2]},
        expected=DECIMAL128_INFINITY,
        msg="Should overflow to decimal infinity for max decimal128 base squared",
    ),
    ExpressionTestCase(
        "one_base_int64_max_exp",
        expression={"$pow": [1, INT64_MAX]},
        expected=Int64(1),
        msg="Should handle one base raised to INT64_MAX",
    ),
    ExpressionTestCase(
        "zero_base_int64_max_exp",
        expression={"$pow": [0, INT64_MAX]},
        expected=Int64(0),
        msg="Should handle zero base raised to INT64_MAX",
    ),
    ExpressionTestCase(
        "double_half_base_squared",
        expression={"$pow": [DOUBLE_HALF, 2]},
        expected=0.25,
        msg="Should handle double half base squared",
    ),
    ExpressionTestCase(
        "double_one_and_half_base_squared",
        expression={"$pow": [DOUBLE_ONE_AND_HALF, 2]},
        expected=2.25,
        msg="Should handle double one and half base squared",
    ),
    ExpressionTestCase(
        "double_just_below_half_squared",
        expression={"$pow": [DOUBLE_JUST_BELOW_HALF, 2]},
        expected=pytest.approx(0.24999999999999942),
        msg="Should handle double just below half squared",
    ),
    ExpressionTestCase(
        "double_just_above_half_squared",
        expression={"$pow": [DOUBLE_JUST_ABOVE_HALF, 2]},
        expected=pytest.approx(0.250000001000000001),
        msg="Should handle double just above half squared",
    ),
    ExpressionTestCase(
        "decimal_half_squared",
        expression={"$pow": [DECIMAL128_HALF, 2]},
        expected=Decimal128("0.2500000000000000000000000000000000"),
        msg="Should return correct result for decimal half squared",
    ),
    ExpressionTestCase(
        "decimal_one_and_half_squared",
        expression={"$pow": [DECIMAL128_ONE_AND_HALF, 2]},
        expected=Decimal128("2.250000000000000000000000000000000"),
        msg="Should return correct result for decimal one and half squared",
    ),
    ExpressionTestCase(
        "decimal_just_below_half_squared",
        expression={"$pow": [DECIMAL128_JUST_BELOW_HALF, 2]},
        expected=Decimal128("0.2499999999999999999999999999999999"),
        msg="Should return correct result for decimal just below half squared",
    ),
    ExpressionTestCase(
        "decimal_just_above_half_squared",
        expression={"$pow": [DECIMAL128_JUST_ABOVE_HALF, 2]},
        expected=Decimal128("0.2500000000000000000000000000000001"),
        msg="Should return correct result for decimal just above half squared",
    ),
    ExpressionTestCase(
        "decimal_precision",
        expression={"$pow": [Decimal128("1.5"), Decimal128("2")]},
        expected=Decimal128("2.250000000000000000000000000000000"),
        msg="Should preserve precision for decimal precision",
    ),
    ExpressionTestCase(
        "decimal_large",
        expression={"$pow": [Decimal128("10"), Decimal128("20")]},
        expected=Decimal128("100000000000000000000.0000000000000"),
        msg="Should return correct result for decimal large",
    ),
    ExpressionTestCase(
        "decimal_two_to_hundred",
        expression={"$pow": [Decimal128("2"), 100]},
        expected=Decimal128("1267650600228229401496703205376.000"),
        msg="Should preserve decimal128 precision for 2^100",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POW_LITERAL_TESTS))
def test_pow_literal(collection, test):
    """Test $pow from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
