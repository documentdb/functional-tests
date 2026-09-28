"""Tests for $ceil at representable-range boundaries for int32, int64, double, and decimal128."""

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
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_PRECISION_LOSS,
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Int32 Boundaries]: $ceil of an integer returns the same integer unchanged.
CEIL_INT32_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_max",
        doc={"value": INT32_MAX},
        expression={"$ceil": ["$value"]},
        expected=INT32_MAX,
        msg="$ceil should return INT32_MAX unchanged",
    ),
    ExpressionTestCase(
        "int32_min",
        doc={"value": INT32_MIN},
        expression={"$ceil": ["$value"]},
        expected=INT32_MIN,
        msg="$ceil should return INT32_MIN unchanged",
    ),
    ExpressionTestCase(
        "int32_overflow",
        doc={"value": INT32_OVERFLOW},
        expression={"$ceil": ["$value"]},
        expected=Int64(INT32_OVERFLOW),
        msg="$ceil should return INT32_OVERFLOW unchanged as int64",
    ),
    ExpressionTestCase(
        "int32_underflow",
        doc={"value": INT32_UNDERFLOW},
        expression={"$ceil": ["$value"]},
        expected=Int64(INT32_UNDERFLOW),
        msg="$ceil should return INT32_UNDERFLOW unchanged as int64",
    ),
]

# Property [Int64 Boundaries]: $ceil of an int64 integer returns the same int64 unchanged.
CEIL_INT64_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_max",
        doc={"value": INT64_MAX},
        expression={"$ceil": ["$value"]},
        expected=INT64_MAX,
        msg="$ceil should return INT64_MAX unchanged",
    ),
    ExpressionTestCase(
        "int64_max_minus_1",
        doc={"value": INT64_MAX_MINUS_1},
        expression={"$ceil": ["$value"]},
        expected=INT64_MAX_MINUS_1,
        msg="$ceil should return INT64_MAX-1 unchanged",
    ),
    ExpressionTestCase(
        "int64_min",
        doc={"value": INT64_MIN},
        expression={"$ceil": ["$value"]},
        expected=INT64_MIN,
        msg="$ceil should return INT64_MIN unchanged",
    ),
    ExpressionTestCase(
        "int64_min_plus_1",
        doc={"value": INT64_MIN_PLUS_1},
        expression={"$ceil": ["$value"]},
        expected=INT64_MIN_PLUS_1,
        msg="$ceil should return INT64_MIN+1 unchanged",
    ),
]

# Property [Double Boundaries]: $ceil rounds double boundary values up to the nearest integer.
CEIL_DOUBLE_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_min_subnormal",
        doc={"value": DOUBLE_MIN_SUBNORMAL},
        expression={"$ceil": ["$value"]},
        expected=1.0,
        msg="$ceil should round the minimum subnormal double up to 1.0",
    ),
    ExpressionTestCase(
        "double_min_negative_subnormal",
        doc={"value": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expression={"$ceil": ["$value"]},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="$ceil should round the minimum negative subnormal double up to negative zero",
    ),
    ExpressionTestCase(
        "double_near_min",
        doc={"value": DOUBLE_NEAR_MIN},
        expression={"$ceil": ["$value"]},
        expected=1.0,
        msg="$ceil should round a near-min double up to 1.0",
    ),
    ExpressionTestCase(
        "double_near_max",
        doc={"value": DOUBLE_NEAR_MAX},
        expression={"$ceil": ["$value"]},
        expected=DOUBLE_NEAR_MAX,
        msg="$ceil should return the same value for a near-max double",
    ),
    ExpressionTestCase(
        "double_max_safe_integer",
        doc={"value": float(DOUBLE_MAX_SAFE_INTEGER)},
        expression={"$ceil": ["$value"]},
        expected=float(DOUBLE_MAX_SAFE_INTEGER),
        msg="$ceil should return the max safe integer double unchanged",
    ),
    ExpressionTestCase(
        "double_precision_loss",
        doc={"value": float(DOUBLE_PRECISION_LOSS)},
        expression={"$ceil": ["$value"]},
        expected=float(DOUBLE_PRECISION_LOSS),
        msg="$ceil should return the precision loss double unchanged",
    ),
    ExpressionTestCase(
        "double_fraction_between_zero_and_one",
        doc={"value": DOUBLE_JUST_BELOW_HALF},
        expression={"$ceil": ["$value"]},
        expected=1.0,
        msg="$ceil should round a double fraction in (0,1) up to 1.0",
    ),
]

# Property [Decimal128 Boundaries]: $ceil rounds decimal128 boundary values up to the nearest
# integer, returning NaN when the value overflows the representable range.
CEIL_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_max",
        doc={"value": DECIMAL128_MAX},
        expression={"$ceil": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$ceil should return NaN for decimal128 max (overflow)",
    ),
    ExpressionTestCase(
        "decimal128_min",
        doc={"value": DECIMAL128_MIN},
        expression={"$ceil": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$ceil should return NaN for decimal128 min (overflow)",
    ),
    ExpressionTestCase(
        "decimal128_large_exponent",
        doc={"value": DECIMAL128_LARGE_EXPONENT},
        expression={"$ceil": ["$value"]},
        expected=DECIMAL128_NAN,
        msg="$ceil should return NaN for a decimal128 with a large exponent (overflow)",
    ),
    ExpressionTestCase(
        "decimal128_small_exponent",
        doc={"value": DECIMAL128_SMALL_EXPONENT},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("1"),
        msg="$ceil should round a decimal128 with a small exponent up to 1",
    ),
    ExpressionTestCase(
        "decimal128_trailing_zero",
        doc={"value": DECIMAL128_TRAILING_ZERO},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("1"),
        msg="$ceil should round a decimal128 with a trailing zero up to 1",
    ),
    ExpressionTestCase(
        "decimal128_many_trailing_zeros",
        doc={"value": DECIMAL128_MANY_TRAILING_ZEROS},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("1"),
        msg="$ceil should round a decimal128 with many trailing zeros up to 1",
    ),
    ExpressionTestCase(
        "decimal128_just_below_half",
        doc={"value": DECIMAL128_JUST_BELOW_HALF},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("1"),
        msg="$ceil should round a decimal128 just below half up to 1",
    ),
    ExpressionTestCase(
        "decimal128_just_above_half",
        doc={"value": DECIMAL128_JUST_ABOVE_HALF},
        expression={"$ceil": ["$value"]},
        expected=Decimal128("1"),
        msg="$ceil should round a decimal128 just above half up to 1",
    ),
]

CEIL_BOUNDARY_ALL_TESTS = (
    CEIL_INT32_BOUNDARY_TESTS
    + CEIL_INT64_BOUNDARY_TESTS
    + CEIL_DOUBLE_BOUNDARY_TESTS
    + CEIL_DECIMAL_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CEIL_BOUNDARY_ALL_TESTS))
def test_ceil_boundaries(collection, test_case: ExpressionTestCase):
    """Test $ceil representable-range boundary cases for all numeric types."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
