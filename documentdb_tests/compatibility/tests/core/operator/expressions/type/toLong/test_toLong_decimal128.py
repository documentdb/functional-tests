"""$toLong Decimal128 conversion tests: zeros, truncation, boundary values, and overflow."""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.type.utils.convert_variants import (  # noqa: E501
    with_convert_variants,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_MAX,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_INT64_UNDERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Decimal128 Conversion]: whole-number Decimal128 values convert exactly,
# fractional values are truncated toward zero, and boundary values at the edges of
# int64 range are accepted.
TOLONG_DECIMAL128_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_whole",
        msg="Whole-number Decimal128 converts to Int64",
        expression={"$toLong": Decimal128("7")},
        expected=Int64(7),
    ),
    ExpressionTestCase(
        "decimal_truncate_positive",
        msg="Positive fractional Decimal128 is truncated toward zero",
        expression={"$toLong": Decimal128("5.5000")},
        expected=Int64(5),
    ),
    ExpressionTestCase(
        "decimal_truncate_negative",
        msg="Negative fractional Decimal128 is truncated toward zero",
        expression={"$toLong": Decimal128("-3.9")},
        expected=Int64(-3),
    ),
    ExpressionTestCase(
        "decimal_negative_zero",
        msg="Decimal128 negative zero converts to Int64(0)",
        expression={"$toLong": DECIMAL128_NEGATIVE_ZERO},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "decimal_trailing_zeros",
        msg="Decimal128 trailing zeros are ignored",
        expression={"$toLong": Decimal128("1.000000000")},
        expected=Int64(1),
    ),
    ExpressionTestCase(
        "decimal_tiny_small_exponent",
        msg="Tiny Decimal128 (1E-6143) is truncated to Int64(0)",
        expression={"$toLong": DECIMAL128_SMALL_EXPONENT},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "decimal_tiny_min_positive",
        msg="Tiny Decimal128 (1E-6176) is truncated to Int64(0)",
        expression={"$toLong": DECIMAL128_MIN_POSITIVE},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "decimal_tiny_max_negative",
        msg="Tiny negative Decimal128 (-1E-6176) is truncated to Int64(0)",
        expression={"$toLong": DECIMAL128_MAX_NEGATIVE},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "decimal_int64_max",
        msg="Exact int64 max as Decimal128 converts to Int64 max",
        expression={"$toLong": DECIMAL128_INT64_MAX},
        expected=INT64_MAX,
    ),
    ExpressionTestCase(
        "decimal_int64_min",
        msg="Exact int64 min as Decimal128 converts to Int64 min",
        expression={"$toLong": Decimal128("-9223372036854775808")},
        expected=INT64_MIN,
    ),
    ExpressionTestCase(
        "decimal_just_below_max_plus_one",
        msg="Decimal128 just below int64 max + 1 truncates to Int64 max",
        expression={"$toLong": Decimal128("9223372036854775807.999")},
        expected=INT64_MAX,
    ),
    ExpressionTestCase(
        "decimal_just_below_min",
        msg="Decimal128 just below int64 min truncates to Int64 min",
        expression={"$toLong": Decimal128("-9223372036854775808.999")},
        expected=INT64_MIN,
    ),
]

# Property [Decimal128 Conversion Errors]: Decimal128 NaN, infinities, and values outside
# int64 range produce a conversion error.
TOLONG_DECIMAL128_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_err_nan",
        msg="Decimal128 NaN is a conversion failure",
        expression={"$toLong": DECIMAL128_NAN},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "decimal_err_pos_infinity",
        msg="Decimal128 Infinity is a conversion failure",
        expression={"$toLong": DECIMAL128_INFINITY},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "decimal_err_neg_infinity",
        msg="Decimal128 -Infinity is a conversion failure",
        expression={"$toLong": DECIMAL128_NEGATIVE_INFINITY},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "decimal_err_overflow_above_max",
        msg="Decimal128 one above int64 max is a conversion failure",
        expression={"$toLong": DECIMAL128_INT64_OVERFLOW},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "decimal_err_overflow_below_min",
        msg="Decimal128 one below int64 min is a conversion failure",
        expression={"$toLong": DECIMAL128_INT64_UNDERFLOW},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "decimal_err_large_exponent",
        msg="Decimal128 with large exponent is a conversion failure",
        expression={"$toLong": DECIMAL128_LARGE_EXPONENT},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "decimal_err_max_value",
        msg="Decimal128 max value is a conversion failure",
        expression={"$toLong": DECIMAL128_MAX},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "decimal_err_min_value",
        msg="Decimal128 min value (negative max) is a conversion failure",
        expression={"$toLong": DECIMAL128_MIN},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOLONG_DECIMAL128_TESTS = TOLONG_DECIMAL128_TESTS + TOLONG_DECIMAL128_ERROR_TESTS


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOLONG_DECIMAL128_TESTS, "$toLong", "long")),
)
def test_toLong_decimal128(collection, test: ExpressionTestCase):
    """$toLong converts Decimal128 values including truncation, boundary values, and overflow."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
