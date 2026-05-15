from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

from .utils.toLower_common import (
    ToLowerTest,
    _expr,
)

# Property [Type Coercion]: non-string coercible types are converted to their string
# representation before lowercasing.
TOLOWER_COERCION_TESTS: list[ToLowerTest] = [
    # int32
    ToLowerTest(
        "coerce_int32", value=42, expected="42", msg="$toLower should coerce int32 to string"
    ),
    ToLowerTest(
        "coerce_int32_zero",
        value=0,
        expected="0",
        msg="$toLower should coerce int32 zero to string",
    ),
    ToLowerTest(
        "coerce_int32_negative",
        value=-123,
        expected="-123",
        msg="$toLower should coerce negative int32 to string",
    ),
    # int64
    ToLowerTest(
        "coerce_int64",
        value=Int64(9_876_543_210),
        expected="9876543210",
        msg="$toLower should coerce int64 to string",
    ),
    ToLowerTest(
        "coerce_int64_max",
        value=INT64_MAX,
        expected="9223372036854775807",
        msg="$toLower should coerce INT64_MAX to string",
    ),
    ToLowerTest(
        "coerce_int64_min",
        value=INT64_MIN,
        expected="-9223372036854775808",
        msg="$toLower should coerce INT64_MIN to string",
    ),
    # double: whole numbers drop trailing .0
    ToLowerTest(
        "coerce_double_whole",
        value=3.0,
        expected="3",
        msg="$toLower should coerce whole double without trailing .0",
    ),
    ToLowerTest(
        "coerce_double_fractional",
        value=3.14,
        expected="3.14",
        msg="$toLower should coerce fractional double to string",
    ),
    # Negative zero preserved.
    ToLowerTest(
        "coerce_double_neg_zero",
        value=DOUBLE_NEGATIVE_ZERO,
        expected="-0",
        msg="$toLower should preserve negative zero in coerced double",
    ),
    # Double precision is limited to 6 significant digits.
    ToLowerTest(
        "coerce_double_precision_limit",
        value=123456.789,
        expected="123457",
        msg="$toLower should round double to 6 significant digits",
    ),
    # Scientific notation for large values (>= 1,000,000).
    ToLowerTest(
        "coerce_double_large_sci",
        value=1e20,
        expected="1e+20",
        msg="$toLower should use lowercase e in scientific notation for large double",
    ),
    ToLowerTest(
        "coerce_double_million",
        value=1_000_000.0,
        expected="1e+06",
        msg="$toLower should use scientific notation for one million",
    ),
    ToLowerTest(
        "coerce_double_below_million",
        value=999_999.0,
        expected="999999",
        msg="$toLower should use decimal notation below one million",
    ),
    # Rounding can push a value across the scientific notation threshold.
    ToLowerTest(
        "coerce_double_round_to_sci",
        value=999_999.5,
        expected="1e+06",
        msg="$toLower should use scientific notation when rounding crosses threshold",
    ),
    # Scientific notation for small values (< 0.0001).
    ToLowerTest(
        "coerce_double_small_sci",
        value=0.000001,
        expected="1e-06",
        msg="$toLower should use scientific notation for small double",
    ),
    ToLowerTest(
        "coerce_double_at_threshold",
        value=0.0001,
        expected="0.0001",
        msg="$toLower should use decimal notation at small threshold",
    ),
    ToLowerTest(
        "coerce_double_below_threshold",
        value=0.00009,
        expected="9e-05",
        msg="$toLower should use scientific notation below small threshold",
    ),
    # Special float values.
    ToLowerTest(
        "coerce_double_nan",
        value=FLOAT_NAN,
        expected="nan",
        msg="$toLower should coerce NaN to lowercase nan",
    ),
    ToLowerTest(
        "coerce_double_inf",
        value=FLOAT_INFINITY,
        expected="inf",
        msg="$toLower should coerce Infinity to lowercase inf",
    ),
    ToLowerTest(
        "coerce_double_neg_inf",
        value=FLOAT_NEGATIVE_INFINITY,
        expected="-inf",
        msg="$toLower should coerce -Infinity to lowercase -inf",
    ),
    # Decimal128 preserves full precision and trailing zeros.
    ToLowerTest(
        "coerce_decimal128",
        value=DECIMAL128_ONE_AND_HALF,
        expected="1.5",
        msg="$toLower should coerce Decimal128 to string",
    ),
    ToLowerTest(
        "coerce_decimal128_trailing",
        value=Decimal128("1.500"),
        expected="1.500",
        msg="$toLower should preserve Decimal128 trailing zeros",
    ),
    ToLowerTest(
        "coerce_decimal128_zero",
        value=DECIMAL128_ZERO,
        expected="0",
        msg="$toLower should coerce Decimal128 zero to string",
    ),
    ToLowerTest(
        "coerce_decimal128_neg_zero",
        value=DECIMAL128_NEGATIVE_ZERO,
        expected="-0",
        msg="$toLower should preserve Decimal128 negative zero",
    ),
    ToLowerTest(
        "coerce_decimal128_negative",
        value=Decimal128("-42.5"),
        expected="-42.5",
        msg="$toLower should coerce negative Decimal128 to string",
    ),
    ToLowerTest(
        "coerce_decimal128_full_precision",
        value=Decimal128("12345678901234567890.1234567890"),
        expected="12345678901234567890.1234567890",
        msg="$toLower should preserve Decimal128 full precision",
    ),
    # Decimal128 special values.
    ToLowerTest(
        "coerce_decimal128_nan",
        value=DECIMAL128_NAN,
        expected="nan",
        msg="$toLower should coerce Decimal128 NaN to lowercase nan",
    ),
    ToLowerTest(
        "coerce_decimal128_inf",
        value=DECIMAL128_INFINITY,
        expected="infinity",
        msg="$toLower should coerce Decimal128 Infinity to lowercase infinity",
    ),
    ToLowerTest(
        "coerce_decimal128_neg_inf",
        value=DECIMAL128_NEGATIVE_INFINITY,
        expected="-infinity",
        msg="$toLower should coerce Decimal128 -Infinity to lowercase -infinity",
    ),
    # Datetime coerced to ISO 8601 with lowercase t and z.
    ToLowerTest(
        "coerce_datetime",
        value=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
        expected="2024-06-15t12:30:45.000z",
        msg="$toLower should coerce datetime to ISO 8601 with lowercase t and z",
    ),
    ToLowerTest(
        "coerce_datetime_epoch",
        value=datetime(1970, 1, 1, tzinfo=timezone.utc),
        expected="1970-01-01t00:00:00.000z",
        msg="$toLower should coerce epoch datetime to ISO 8601",
    ),
    ToLowerTest(
        "coerce_datetime_millis",
        value=datetime(2024, 6, 15, 12, 30, 45, 123_000, tzinfo=timezone.utc),
        expected="2024-06-15t12:30:45.123z",
        msg="$toLower should coerce datetime with milliseconds",
    ),
    # Timestamp coerced to custom format with month abbreviation lowercased.
    ToLowerTest(
        "coerce_timestamp_single_digit_day",
        value=Timestamp(1704067200, 1),
        expected="jan  1 00:00:00:1",
        msg="$toLower should coerce Timestamp with single-digit day",
    ),
    ToLowerTest(
        "coerce_timestamp_double_digit_day",
        value=Timestamp(1721500800, 1),
        expected="jul 20 18:40:00:1",
        msg="$toLower should coerce Timestamp with double-digit day",
    ),
    ToLowerTest(
        "coerce_timestamp_increment",
        value=Timestamp(1704067200, 42),
        expected="jan  1 00:00:00:42",
        msg="$toLower should coerce Timestamp preserving increment",
    ),
    # Code (without scope) coerced to its code string before lowercasing.
    ToLowerTest(
        "coerce_code",
        value=Code("function() { return HELLO; }"),
        expected="function() { return hello; }",
        msg="$toLower should coerce Code and lowercase its content",
    ),
    # Integer boundary values.
    ToLowerTest(
        "coerce_int32_max",
        value=INT32_MAX,
        expected="2147483647",
        msg="$toLower should coerce INT32_MAX to string",
    ),
    ToLowerTest(
        "coerce_int32_min",
        value=INT32_MIN,
        expected="-2147483648",
        msg="$toLower should coerce INT32_MIN to string",
    ),
    # Float boundary values.
    ToLowerTest(
        "coerce_subnormal_double",
        value=DOUBLE_MIN_SUBNORMAL,
        expected="4.94066e-324",
        msg="$toLower should coerce subnormal double to string",
    ),
    ToLowerTest(
        "coerce_max_double",
        value=DOUBLE_MAX,
        expected="1.79769e+308",
        msg="$toLower should coerce near-max double to string",
    ),
    # Decimal128 boundary values.
    ToLowerTest(
        "coerce_decimal128_max_precision",
        value=Decimal128("1234567890123456789012345678901234"),
        expected="1234567890123456789012345678901234",
        msg="$toLower should preserve Decimal128 34-digit precision",
    ),
    ToLowerTest(
        "coerce_decimal128_extreme_exponent",
        value=DECIMAL128_LARGE_EXPONENT,
        expected="1.000000000000000000000000000000000e+6144",
        msg="$toLower should lowercase Decimal128 large exponent notation",
    ),
    ToLowerTest(
        "coerce_decimal128_tiny_exponent",
        value=DECIMAL128_MIN_POSITIVE,
        expected="1e-6176",
        msg="$toLower should lowercase Decimal128 tiny exponent notation",
    ),
    ToLowerTest(
        "coerce_decimal128_max_negative",
        value=DECIMAL128_MAX_NEGATIVE,
        expected="-1e-6176",
        msg="$toLower should lowercase Decimal128 maximum negative value",
    ),
    # Datetime boundary values.
    ToLowerTest(
        "coerce_datetime_pre_epoch",
        value=datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        expected="1969-12-31t23:59:59.000z",
        msg="$toLower should coerce pre-epoch datetime to ISO 8601",
    ),
    ToLowerTest(
        "coerce_datetime_far_future",
        value=datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        expected="9999-12-31t23:59:59.000z",
        msg="$toLower should coerce far-future datetime to ISO 8601",
    ),
    # Timestamp boundary values.
    ToLowerTest(
        "coerce_timestamp_zero",
        value=Timestamp(0, 0),
        expected="jan  1 00:00:00:0",
        msg="$toLower should coerce zero Timestamp to epoch",
    ),
    ToLowerTest(
        "coerce_timestamp_max_increment",
        value=Timestamp(0, 2**32 - 1),
        expected="jan  1 00:00:00:4294967295",
        msg="$toLower should coerce Timestamp with max increment",
    ),
    ToLowerTest(
        "coerce_timestamp_max_time",
        value=Timestamp(2**32 - 1, 1),
        expected="feb  7 06:28:15:1",
        msg="$toLower should coerce Timestamp with max time value",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOLOWER_COERCION_TESTS))
def test_tolower_coercion(collection, test_case: ToLowerTest):
    """Test $toLower type coercion behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
