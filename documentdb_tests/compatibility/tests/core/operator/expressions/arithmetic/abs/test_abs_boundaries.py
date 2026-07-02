"""Tests for $abs at representable-range boundaries, including overflow and underflow."""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_PRECISION_LOSS,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN_PLUS_1,
)

# Property [Int32 Boundaries]: $abs at int32 limits returns the magnitude, promoting to long when
# the result overflows int32.
ABS_INT32_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max",
        doc={"value": INT32_MAX},
        expression={"$abs": ["$value"]},
        expected=INT32_MAX,
        msg="$abs should return INT32_MAX for INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_max_minus_1",
        doc={"value": INT32_MAX_MINUS_1},
        expression={"$abs": ["$value"]},
        expected=INT32_MAX_MINUS_1,
        msg="$abs should return INT32_MAX-1 for INT32_MAX-1",
    ),
    ExpressionTestCase(
        "int32_min_plus_1",
        doc={"value": INT32_MIN_PLUS_1},
        expression={"$abs": ["$value"]},
        expected=INT32_MAX,
        msg="$abs should return INT32_MAX for INT32_MIN+1",
    ),
    ExpressionTestCase(
        "int32_min",
        doc={"value": INT32_MIN},
        expression={"$abs": ["$value"]},
        expected=Int64(INT32_OVERFLOW),
        msg="$abs should promote to int64 for INT32_MIN",
    ),
    ExpressionTestCase(
        "int32_overflow",
        doc={"value": INT32_OVERFLOW},
        expression={"$abs": ["$value"]},
        expected=Int64(INT32_OVERFLOW),
        msg="$abs should return the same long value for INT32_OVERFLOW",
    ),
    ExpressionTestCase(
        "int32_underflow",
        doc={"value": INT32_UNDERFLOW},
        expression={"$abs": ["$value"]},
        expected=Int64(-INT32_UNDERFLOW),
        msg="$abs should return the negated long value for INT32_UNDERFLOW",
    ),
]

# Property [Int64 Boundaries]: $abs at int64 limits returns the magnitude as a long.
ABS_INT64_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_max",
        doc={"value": INT64_MAX},
        expression={"$abs": ["$value"]},
        expected=INT64_MAX,
        msg="$abs should return INT64_MAX for INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        doc={"value": INT64_MAX_MINUS_1},
        expression={"$abs": ["$value"]},
        expected=INT64_MAX_MINUS_1,
        msg="$abs should return INT64_MAX-1 for INT64_MAX-1",
    ),
    ExpressionTestCase(
        "int64_min_plus_1",
        doc={"value": INT64_MIN_PLUS_1},
        expression={"$abs": ["$value"]},
        expected=INT64_MAX,
        msg="$abs should return INT64_MAX for INT64_MIN+1",
    ),
]

# Property [Double Boundaries]: $abs preserves double magnitude across the representable range.
ABS_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_min_subnormal",
        doc={"value": DOUBLE_MIN_SUBNORMAL},
        expression={"$abs": ["$value"]},
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="$abs should return the same value for the minimum subnormal double",
    ),
    ExpressionTestCase(
        "double_min_negative_subnormal",
        doc={"value": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expression={"$abs": ["$value"]},
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="$abs should return the positive subnormal for the minimum negative subnormal double",
    ),
    ExpressionTestCase(
        "double_near_min",
        doc={"value": DOUBLE_NEAR_MIN},
        expression={"$abs": ["$value"]},
        expected=DOUBLE_NEAR_MIN,
        msg="$abs should return the same value for a near-min double",
    ),
    ExpressionTestCase(
        "double_near_max",
        doc={"value": DOUBLE_NEAR_MAX},
        expression={"$abs": ["$value"]},
        expected=DOUBLE_NEAR_MAX,
        msg="$abs should return the same value for a near-max double",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        doc={"value": float(DOUBLE_MAX_SAFE_INTEGER)},
        expression={"$abs": ["$value"]},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="$abs should return the same value for the max safe integer double",
    ),
    ExpressionTestCase(
        "double_precision_loss",
        doc={"value": float(DOUBLE_PRECISION_LOSS)},
        expression={"$abs": ["$value"]},
        expected=float(DOUBLE_PRECISION_LOSS),
        msg="$abs should return the same value for a precision loss double",
    ),
    ExpressionTestCase(
        "double_just_below_half",
        doc={"value": DOUBLE_JUST_BELOW_HALF},
        expression={"$abs": ["$value"]},
        expected=DOUBLE_JUST_BELOW_HALF,
        msg="$abs should return the same value for a double just below half",
    ),
    ExpressionTestCase(
        "double_just_above_half",
        doc={"value": DOUBLE_JUST_ABOVE_HALF},
        expression={"$abs": ["$value"]},
        expected=DOUBLE_JUST_ABOVE_HALF,
        msg="$abs should return the same value for a double just above half",
    ),
]

# Property [Decimal128 Boundaries]: $abs preserves decimal128 magnitude and precision, including
# trailing zeros.
ABS_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_max",
        doc={"value": DECIMAL128_MAX},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_MAX,
        msg="$abs should return the same value for decimal128 max",
    ),
    ExpressionTestCase(
        "decimal128_min",
        doc={"value": DECIMAL128_MIN},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_MAX,
        msg="$abs should return decimal128 max for decimal128 min",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        doc={"value": DECIMAL128_LARGE_EXPONENT},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="$abs should return the same value for a decimal128 with a large exponent",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent",
        doc={"value": DECIMAL128_SMALL_EXPONENT},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="$abs should return the same value for a decimal128 with a small exponent",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        doc={"value": DECIMAL128_TRAILING_ZERO},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_TRAILING_ZERO,
        msg="$abs should preserve a decimal128 trailing zero",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        doc={"value": DECIMAL128_MANY_TRAILING_ZEROS},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_MANY_TRAILING_ZEROS,
        msg="$abs should preserve decimal128 many trailing zeros",
    ),
    ExpressionTestCase(
        "decimal128_just_below_half",
        doc={"value": DECIMAL128_JUST_BELOW_HALF},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_JUST_BELOW_HALF,
        msg="$abs should return the same value for a decimal128 just below half",
    ),
    ExpressionTestCase(
        "decimal128_just_above_half",
        doc={"value": DECIMAL128_JUST_ABOVE_HALF},
        expression={"$abs": ["$value"]},
        expected=DECIMAL128_JUST_ABOVE_HALF,
        msg="$abs should return the same value for a decimal128 just above half",
    ),
]

ABS_BOUNDARY_ALL_TESTS = (
    ABS_INT32_BOUNDARY_TESTS
    + ABS_INT64_BOUNDARY_TESTS
    + ABS_DOUBLE_BOUNDARY_TESTS
    + ABS_DECIMAL_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ABS_BOUNDARY_ALL_TESTS))
def test_abs_boundaries(collection, test_case: ExpressionTestCase):
    """Test $abs representable-range boundary cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
