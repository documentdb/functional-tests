"""Tests for $floor at representable-range, subnormal, and decimal128 exponent boundaries."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

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
    DECIMAL128_NAN,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_ZERO,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Integer Boundaries]: floor preserves integer-type values at representable-range
# boundaries, and a value just past the int32 range stays a long.
FLOOR_INT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "boundary_int32_max",
        doc={"value": INT32_MAX},
        expression={"$floor": ["$value"]},
        expected=INT32_MAX,
        msg="$floor should return INT32_MAX unchanged as an int",
    ),
    ExpressionTestCase(
        "boundary_int32_min",
        doc={"value": INT32_MIN},
        expression={"$floor": ["$value"]},
        expected=INT32_MIN,
        msg="$floor should return INT32_MIN unchanged as an int",
    ),
    ExpressionTestCase(
        "boundary_int32_overflow",
        doc={"value": INT32_OVERFLOW},
        expression={"$floor": ["$value"]},
        expected=Int64(INT32_OVERFLOW),
        msg="$floor should return a value just above the int32 range unchanged as a long",
    ),
    ExpressionTestCase(
        "boundary_int32_underflow",
        doc={"value": INT32_UNDERFLOW},
        expression={"$floor": ["$value"]},
        expected=Int64(INT32_UNDERFLOW),
        msg="$floor should return a value just below the int32 range unchanged as a long",
    ),
    ExpressionTestCase(
        "boundary_int64_max",
        doc={"value": INT64_MAX},
        expression={"$floor": ["$value"]},
        expected=INT64_MAX,
        msg="$floor should return INT64_MAX unchanged as a long",
    ),
    ExpressionTestCase(
        "boundary_int64_max_minus_1",
        doc={"value": INT64_MAX_MINUS_1},
        expression={"$floor": ["$value"]},
        expected=INT64_MAX_MINUS_1,
        msg="$floor should return INT64_MAX-1 unchanged as a long",
    ),
    ExpressionTestCase(
        "boundary_int64_min",
        doc={"value": INT64_MIN},
        expression={"$floor": ["$value"]},
        expected=INT64_MIN,
        msg="$floor should return INT64_MIN unchanged as a long",
    ),
    ExpressionTestCase(
        "boundary_int64_min_plus_1",
        doc={"value": INT64_MIN_PLUS_1},
        expression={"$floor": ["$value"]},
        expected=INT64_MIN_PLUS_1,
        msg="$floor should return INT64_MIN+1 unchanged as a long",
    ),
]

# Property [Double Boundaries]: floor handles subnormal and extreme double magnitudes,
# including values on either side of the 0.5 rounding boundary.
FLOOR_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "boundary_double_min_subnormal",
        doc={"value": DOUBLE_MIN_SUBNORMAL},
        expression={"$floor": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$floor should floor the smallest positive subnormal double to DOUBLE_ZERO",
    ),
    ExpressionTestCase(
        "boundary_double_min_negative_subnormal",
        doc={"value": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expression={"$floor": ["$value"]},
        expected=-1.0,
        msg="$floor should floor the smallest negative subnormal double to -1.0",
    ),
    ExpressionTestCase(
        "boundary_double_near_min",
        doc={"value": DOUBLE_NEAR_MIN},
        expression={"$floor": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$floor should floor a near-min positive double to DOUBLE_ZERO",
    ),
    ExpressionTestCase(
        "boundary_double_near_max",
        doc={"value": DOUBLE_NEAR_MAX},
        expression={"$floor": ["$value"]},
        expected=DOUBLE_NEAR_MAX,
        msg="$floor should return a near-max whole-magnitude double unchanged",
    ),
    ExpressionTestCase(
        "boundary_double_just_below_half",
        doc={"value": DOUBLE_JUST_BELOW_HALF},
        expression={"$floor": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$floor should floor a double just below 0.5 to DOUBLE_ZERO",
    ),
    ExpressionTestCase(
        "boundary_double_just_above_half",
        doc={"value": DOUBLE_JUST_ABOVE_HALF},
        expression={"$floor": ["$value"]},
        expected=DOUBLE_ZERO,
        msg="$floor should floor a double just above 0.5 to DOUBLE_ZERO",
    ),
]

# Property [Decimal Boundaries]: floor handles decimal128 exponent extremes, trailing-zero
# normalization, and values around the 0.5 boundary, returning NaN when the magnitude overflows.
FLOOR_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "boundary_decimal_max",
        doc={"value": DECIMAL128_MAX},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$floor should return NaN for the maximum decimal128 magnitude",
    ),
    ExpressionTestCase(
        "boundary_decimal_min",
        doc={"value": DECIMAL128_MIN},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$floor should return NaN for the minimum decimal128 magnitude",
    ),
    ExpressionTestCase(
        "boundary_decimal_large_exponent",
        doc={"value": DECIMAL128_LARGE_EXPONENT},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$floor should return NaN for a decimal128 with a large positive exponent",
    ),
    ExpressionTestCase(
        "boundary_decimal_small_exponent",
        doc={"value": DECIMAL128_SMALL_EXPONENT},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$floor should floor a decimal128 with a large negative exponent to 0",
    ),
    ExpressionTestCase(
        "boundary_decimal_trailing_zero",
        doc={"value": DECIMAL128_TRAILING_ZERO},
        expression={"$floor": ["$value"]},
        expected=Decimal128("1"),
        msg="$floor should normalize a whole decimal128 with a trailing zero to 1",
    ),
    ExpressionTestCase(
        "boundary_decimal_many_trailing_zeros",
        doc={"value": DECIMAL128_MANY_TRAILING_ZEROS},
        expression={"$floor": ["$value"]},
        expected=Decimal128("1"),
        msg="$floor should normalize a whole decimal128 with many trailing zeros to 1",
    ),
    ExpressionTestCase(
        "boundary_decimal_just_below_half",
        doc={"value": DECIMAL128_JUST_BELOW_HALF},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$floor should floor a decimal128 just below 0.5 to 0",
    ),
    ExpressionTestCase(
        "boundary_decimal_just_above_half",
        doc={"value": DECIMAL128_JUST_ABOVE_HALF},
        expression={"$floor": ["$value"]},
        expected=DECIMAL128_ZERO,
        msg="$floor should floor a decimal128 just above 0.5 to 0",
    ),
]

FLOOR_BOUNDARY_TESTS = (
    FLOOR_INT_BOUNDARY_TESTS + FLOOR_DOUBLE_BOUNDARY_TESTS + FLOOR_DECIMAL_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(FLOOR_BOUNDARY_TESTS))
def test_floor_boundaries(collection, test):
    """Test $floor at numeric boundaries."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
