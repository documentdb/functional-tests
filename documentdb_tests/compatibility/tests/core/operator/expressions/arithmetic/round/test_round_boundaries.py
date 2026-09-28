"""
Precision and boundary tests for $round expression.

Covers IEEE-754 double vs Decimal128 rounding precision, INT32/INT64
boundary values, double subnormals, and Decimal128 max/min/exponents
and trailing-zero normalization.
"""

import pytest
from bson import (
    Decimal128,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

ROUND_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_precision_1_005",
        expression={"$round": [Decimal128("1.005"), 2]},
        expected=Decimal128("1.00"),
        msg="decimal128 stores 1.005 exactly; half-to-even rounds to 1.00 at place 2",
    ),
    ExpressionTestCase(
        "double_precision_2_015",
        expression={"$round": [2.015, 2]},
        expected=2.02,
        msg="double 2.015 rounds to 2.02 at place 2",
    ),
    ExpressionTestCase(
        "decimal_precision_2_015",
        expression={"$round": [Decimal128("2.015"), 2]},
        expected=Decimal128("2.02"),
        msg="decimal128 2.015 rounds to 2.02 at place 2",
    ),
    ExpressionTestCase(
        "int32_max",
        expression={"$round": INT32_MAX},
        expected=INT32_MAX,
        msg="int32 max is integral and returned unchanged (type preserved)",
    ),
    ExpressionTestCase(
        "int32_min",
        expression={"$round": INT32_MIN},
        expected=INT32_MIN,
        msg="int32 min is integral and returned unchanged",
    ),
    ExpressionTestCase(
        "int64_max",
        expression={"$round": INT64_MAX},
        expected=INT64_MAX,
        msg="int64 max is integral and returned unchanged (type preserved)",
    ),
    ExpressionTestCase(
        "int64_min",
        expression={"$round": INT64_MIN},
        expected=INT64_MIN,
        msg="int64 min is integral and returned unchanged",
    ),
    ExpressionTestCase(
        "double_min_subnormal",
        expression={"$round": DOUBLE_MIN_SUBNORMAL},
        expected=0.0,
        msg="smallest subnormal double rounds to 0.0",
    ),
    ExpressionTestCase(
        "double_near_min",
        expression={"$round": DOUBLE_NEAR_MIN},
        expected=0.0,
        msg="tiny normal double (1e-308) rounds to 0.0",
    ),
    ExpressionTestCase(
        "double_near_max",
        expression={"$round": DOUBLE_NEAR_MAX},
        expected=DOUBLE_NEAR_MAX,
        msg="huge double (1e308) has no fractional part and is unchanged",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        expression={"$round": float(DOUBLE_MAX_SAFE_INTEGER)},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="2^53 max-safe-integer double is integral and unchanged",
    ),
    ExpressionTestCase(
        "decimal128_max",
        expression={"$round": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
        msg="decimal128 max magnitude has no fractional part and is unchanged",
    ),
    ExpressionTestCase(
        "decimal128_min",
        expression={"$round": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
        msg="decimal128 min magnitude has no fractional part and is unchanged",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent",
        expression={"$round": DECIMAL128_SMALL_EXPONENT},
        expected=Decimal128("0"),
        msg="very small decimal128 (1E-6143) rounds to 0",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        expression={"$round": DECIMAL128_LARGE_EXPONENT},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="very large decimal128 (1E+6144) is unchanged",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        expression={"$round": DECIMAL128_TRAILING_ZERO},
        expected=Decimal128("1"),
        msg="rounding normalizes decimal 1.0 to 1",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        expression={"$round": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=Decimal128("1"),
        msg="rounding normalizes decimal 1.000... to 1",
    ),
]

ROUND_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_precision_2_015",
        expression={"$round": ["$value", "$place"]},
        doc={"value": Decimal128("2.015"), "place": 2},
        expected=Decimal128("2.02"),
        msg="decimal128 2.015 rounds to 2.02 at place 2",
    ),
    ExpressionTestCase(
        "int32_max",
        expression={"$round": "$value"},
        doc={"value": INT32_MAX},
        expected=INT32_MAX,
        msg="int32 max is integral and returned unchanged (type preserved)",
    ),
    ExpressionTestCase(
        "int64_min",
        expression={"$round": "$value"},
        doc={"value": INT64_MIN},
        expected=INT64_MIN,
        msg="int64 min is integral and returned unchanged",
    ),
    ExpressionTestCase(
        "double_min_subnormal",
        expression={"$round": "$value"},
        doc={"value": DOUBLE_MIN_SUBNORMAL},
        expected=0.0,
        msg="smallest subnormal double rounds to 0.0",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        expression={"$round": "$value"},
        doc={"value": DECIMAL128_LARGE_EXPONENT},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="very large decimal128 (1E+6144) is unchanged",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ROUND_LITERAL_TESTS))
def test_round_literal(collection, test):
    """Test $round with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ROUND_INSERT_TESTS))
def test_round_insert(collection, test):
    """Test $round with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
