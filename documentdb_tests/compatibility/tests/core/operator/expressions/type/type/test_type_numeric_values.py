"""$type numeric value tests.

Tests that $type returns the correct BSON type name for special and boundary
numeric values, including NaN, infinities, negative zero, and type extremes.
"""

from __future__ import annotations

import pytest
from bson import Int64

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
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MIN,
)

# Property [Special Numeric Values]: special float and Decimal128 values
# (NaN, infinity, negative zero) return their base numeric type name.
TYPE_SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "special_float_nan",
        expression={"$type": FLOAT_NAN},
        expected="double",
        msg="$type should return 'double' for float NaN",
    ),
    ExpressionTestCase(
        "special_float_inf",
        expression={"$type": FLOAT_INFINITY},
        expected="double",
        msg="$type should return 'double' for float infinity",
    ),
    ExpressionTestCase(
        "special_float_neg_inf",
        expression={"$type": FLOAT_NEGATIVE_INFINITY},
        expected="double",
        msg="$type should return 'double' for float negative infinity",
    ),
    ExpressionTestCase(
        "special_float_neg_zero",
        expression={"$type": DOUBLE_NEGATIVE_ZERO},
        expected="double",
        msg="$type should return 'double' for float negative zero",
    ),
    ExpressionTestCase(
        "special_float_zero",
        expression={"$type": DOUBLE_ZERO},
        expected="double",
        msg="$type should return 'double' for float positive zero",
    ),
    ExpressionTestCase(
        "special_decimal_nan",
        expression={"$type": DECIMAL128_NAN},
        expected="decimal",
        msg="$type should return 'decimal' for Decimal128 NaN",
    ),
    ExpressionTestCase(
        "special_decimal_inf",
        expression={"$type": DECIMAL128_INFINITY},
        expected="decimal",
        msg="$type should return 'decimal' for Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "special_decimal_neg_inf",
        expression={"$type": DECIMAL128_NEGATIVE_INFINITY},
        expected="decimal",
        msg="$type should return 'decimal' for Decimal128 negative Infinity",
    ),
    ExpressionTestCase(
        "special_decimal_neg_zero",
        expression={"$type": DECIMAL128_NEGATIVE_ZERO},
        expected="decimal",
        msg="$type should return 'decimal' for Decimal128 negative zero",
    ),
    ExpressionTestCase(
        "special_decimal_zero",
        expression={"$type": DECIMAL128_ZERO},
        expected="decimal",
        msg="$type should return 'decimal' for Decimal128 positive zero",
    ),
]

# Property [Numeric Boundary Values]: numeric types at their boundary values
# still return the correct BSON type name.
TYPE_NUMERIC_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "boundary_int32_max",
        expression={"$type": INT32_MAX},
        expected="int",
        msg="$type should return 'int' for int32 max value",
    ),
    ExpressionTestCase(
        "boundary_int32_min",
        expression={"$type": INT32_MIN},
        expected="int",
        msg="$type should return 'int' for int32 min value",
    ),
    ExpressionTestCase(
        "boundary_int64_max",
        expression={"$type": INT64_MAX},
        expected="long",
        msg="$type should return 'long' for int64 max value",
    ),
    ExpressionTestCase(
        "boundary_int64_min",
        expression={"$type": INT64_MIN},
        expected="long",
        msg="$type should return 'long' for int64 min value",
    ),
    ExpressionTestCase(
        "boundary_int32_overflow",
        expression={"$type": Int64(INT32_OVERFLOW)},
        expected="long",
        msg="$type should return 'long' for int32 overflow value as int64",
    ),
    ExpressionTestCase(
        "boundary_int32_underflow",
        expression={"$type": Int64(INT32_UNDERFLOW)},
        expected="long",
        msg="$type should return 'long' for int32 underflow value as int64",
    ),
    ExpressionTestCase(
        "boundary_double_max",
        expression={"$type": DOUBLE_MAX},
        expected="double",
        msg="$type should return 'double' for the maximum double value",
    ),
    ExpressionTestCase(
        "boundary_double_min",
        expression={"$type": DOUBLE_MIN},
        expected="double",
        msg="$type should return 'double' for the minimum double value",
    ),
    ExpressionTestCase(
        "boundary_double_min_subnormal",
        expression={"$type": DOUBLE_MIN_SUBNORMAL},
        expected="double",
        msg="$type should return 'double' for the smallest positive subnormal double",
    ),
    ExpressionTestCase(
        "boundary_double_min_neg_subnormal",
        expression={"$type": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected="double",
        msg="$type should return 'double' for the smallest negative subnormal double",
    ),
    ExpressionTestCase(
        "boundary_decimal_max",
        expression={"$type": DECIMAL128_MAX},
        expected="decimal",
        msg="$type should return 'decimal' for Decimal128 at max exponent",
    ),
    ExpressionTestCase(
        "boundary_decimal_min",
        expression={"$type": DECIMAL128_MIN},
        expected="decimal",
        msg="$type should return 'decimal' for Decimal128 at min exponent",
    ),
    ExpressionTestCase(
        "boundary_decimal_min_positive",
        expression={"$type": DECIMAL128_MIN_POSITIVE},
        expected="decimal",
        msg="$type should return 'decimal' for the smallest positive Decimal128",
    ),
    ExpressionTestCase(
        "boundary_decimal_max_negative",
        expression={"$type": DECIMAL128_MAX_NEGATIVE},
        expected="decimal",
        msg="$type should return 'decimal' for the largest negative Decimal128",
    ),
]

TYPE_NUMERIC_VALUE_TESTS = TYPE_SPECIAL_NUMERIC_TESTS + TYPE_NUMERIC_BOUNDARY_TESTS


@pytest.mark.parametrize("test", pytest_params(TYPE_NUMERIC_VALUE_TESTS))
def test_type_numeric_values(collection, test: ExpressionTestCase):
    """$type returns the correct type name for special and boundary numeric values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
