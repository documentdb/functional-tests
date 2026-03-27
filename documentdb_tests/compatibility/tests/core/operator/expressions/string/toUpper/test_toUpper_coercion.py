from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, Timestamp

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
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
from documentdb_tests.compatibility.tests.core.operator.expressions.string.toUpper.utils.toUpper_common import (
    ToUpperTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Type Coercion]: numeric, datetime, timestamp, Code, and Symbol values are coerced to
# their string representation before uppercasing.
TOUPPER_COERCION_TESTS: list[ToUpperTest] = [
    # int32.
    ToUpperTest(
        "coerce_int32", value=42, expected="42", msg="$toUpper should coerce int32 to string"
    ),
    ToUpperTest(
        "coerce_int32_neg",
        value=-42,
        expected="-42",
        msg="$toUpper should coerce negative int32 to string",
    ),
    # int64.
    ToUpperTest(
        "coerce_int64", value=Int64(42), expected="42", msg="$toUpper should coerce int64 to string"
    ),
    ToUpperTest(
        "coerce_int64_neg",
        value=Int64(-42),
        expected="-42",
        msg="$toUpper should coerce negative int64 to string",
    ),
    # double: whole numbers drop trailing .0.
    ToUpperTest(
        "coerce_double_whole",
        value=3.0,
        expected="3",
        msg="$toUpper should coerce whole double without trailing .0",
    ),
    ToUpperTest(
        "coerce_double_fractional",
        value=3.14,
        expected="3.14",
        msg="$toUpper should coerce fractional double to string",
    ),
    # Negative zero preserved.
    ToUpperTest(
        "coerce_double_neg_zero",
        value=DOUBLE_NEGATIVE_ZERO,
        expected="-0",
        msg="$toUpper should preserve negative zero in coerced double",
    ),
    # Scientific notation uses uppercase E.
    ToUpperTest(
        "coerce_double_sci_large",
        value=1e20,
        expected="1E+20",
        msg="$toUpper should use uppercase E in scientific notation for large double",
    ),
    ToUpperTest(
        "coerce_double_sci_small",
        value=0.000001,
        expected="1E-06",
        msg="$toUpper should use uppercase E in scientific notation for small double",
    ),
    # Double precision limited to approximately 6 significant digits.
    ToUpperTest(
        "coerce_double_six_digits",
        value=999999.0,
        expected="999999",
        msg="$toUpper should preserve 6 significant digits for double",
    ),
    ToUpperTest(
        "coerce_double_seven_digits",
        value=1_000_000.0,
        expected="1E+06",
        msg="$toUpper should use scientific notation for double with 7 digits",
    ),
    # Special float values.
    ToUpperTest(
        "coerce_double_nan",
        value=FLOAT_NAN,
        expected="NAN",
        msg="$toUpper should coerce NaN to uppercase NAN",
    ),
    ToUpperTest(
        "coerce_double_inf",
        value=FLOAT_INFINITY,
        expected="INF",
        msg="$toUpper should coerce Infinity to uppercase INF",
    ),
    ToUpperTest(
        "coerce_double_neg_inf",
        value=FLOAT_NEGATIVE_INFINITY,
        expected="-INF",
        msg="$toUpper should coerce -Infinity to uppercase -INF",
    ),
    # Decimal128 preserves full precision and trailing zeros.
    ToUpperTest(
        "coerce_decimal",
        value=Decimal128("3.14"),
        expected="3.14",
        msg="$toUpper should coerce Decimal128 to string",
    ),
    ToUpperTest(
        "coerce_decimal_trailing",
        value=Decimal128("3.1400"),
        expected="3.1400",
        msg="$toUpper should preserve Decimal128 trailing zeros",
    ),
    ToUpperTest(
        "coerce_decimal_neg_zero",
        value=DECIMAL128_NEGATIVE_ZERO,
        expected="-0",
        msg="$toUpper should preserve Decimal128 negative zero",
    ),
    # Decimal128 special values.
    ToUpperTest(
        "coerce_decimal_nan",
        value=DECIMAL128_NAN,
        expected="NAN",
        msg="$toUpper should coerce Decimal128 NaN to uppercase NAN",
    ),
    ToUpperTest(
        "coerce_decimal_inf",
        value=DECIMAL128_INFINITY,
        expected="INFINITY",
        msg="$toUpper should coerce Decimal128 Infinity to uppercase INFINITY",
    ),
    ToUpperTest(
        "coerce_decimal_neg_inf",
        value=DECIMAL128_NEGATIVE_INFINITY,
        expected="-INFINITY",
        msg="$toUpper should coerce Decimal128 -Infinity to uppercase -INFINITY",
    ),
    # Datetime coerced to ISO 8601 format.
    ToUpperTest(
        "coerce_datetime",
        value=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
        expected="2024-06-15T12:30:45.000Z",
        msg="$toUpper should coerce datetime to ISO 8601 string",
    ),
    # Timestamp coerced to custom format with uppercased month abbreviation.
    ToUpperTest(
        "coerce_timestamp",
        value=Timestamp(1, 1),
        expected="JAN  1 00:00:01:1",
        msg="$toUpper should coerce Timestamp to uppercased month format",
    ),
    ToUpperTest(
        "coerce_timestamp_feb",
        value=Timestamp(1707000000, 1),
        expected="FEB  3 22:40:00:1",
        msg="$toUpper should coerce Timestamp with February date",
    ),
    # JavaScript Code coerced to its code string before uppercasing.
    ToUpperTest(
        "coerce_code",
        value=Code("hello"),
        expected="HELLO",
        msg="$toUpper should coerce Code to uppercased string",
    ),
    ToUpperTest(
        "coerce_code_function",
        value=Code("function() { return x; }"),
        expected="FUNCTION() { RETURN X; }",
        msg="$toUpper should uppercase Code function body",
    ),
    # Integer boundary values.
    ToUpperTest(
        "coerce_max_int32",
        value=INT32_MAX,
        expected="2147483647",
        msg="$toUpper should coerce INT32_MAX to string",
    ),
    ToUpperTest(
        "coerce_min_int32",
        value=INT32_MIN,
        expected="-2147483648",
        msg="$toUpper should coerce INT32_MIN to string",
    ),
    ToUpperTest(
        "coerce_max_int64",
        value=INT64_MAX,
        expected="9223372036854775807",
        msg="$toUpper should coerce INT64_MAX to string",
    ),
    ToUpperTest(
        "coerce_min_int64",
        value=INT64_MIN,
        expected="-9223372036854775808",
        msg="$toUpper should coerce INT64_MIN to string",
    ),
    # Float boundary values.
    ToUpperTest(
        "coerce_subnormal",
        value=DOUBLE_MIN_SUBNORMAL,
        expected="4.94066E-324",
        msg="$toUpper should coerce subnormal double to string",
    ),
    ToUpperTest(
        "coerce_max_double",
        value=DOUBLE_MAX,
        expected="1.79769E+308",
        msg="$toUpper should coerce near-max double to string",
    ),
    # Decimal128 boundary values.
    ToUpperTest(
        "coerce_decimal_max_precision",
        value=Decimal128("1234567890123456789012345678901234"),
        expected="1234567890123456789012345678901234",
        msg="$toUpper should preserve Decimal128 34-digit precision",
    ),
    ToUpperTest(
        "coerce_decimal_large_exp",
        value=DECIMAL128_LARGE_EXPONENT,
        expected="1.000000000000000000000000000000000E+6144",
        msg="$toUpper should preserve Decimal128 large exponent",
    ),
    ToUpperTest(
        "coerce_decimal_small_exp",
        value=DECIMAL128_MIN_POSITIVE,
        expected="1E-6176",
        msg="$toUpper should preserve Decimal128 small exponent",
    ),
    ToUpperTest(
        "coerce_decimal_max_negative",
        value=DECIMAL128_MAX_NEGATIVE,
        expected="-1E-6176",
        msg="$toUpper should preserve Decimal128 maximum negative value",
    ),
    # Datetime boundary values.
    ToUpperTest(
        "coerce_datetime_epoch",
        value=datetime(1970, 1, 1, tzinfo=timezone.utc),
        expected="1970-01-01T00:00:00.000Z",
        msg="$toUpper should coerce epoch datetime to ISO 8601",
    ),
    ToUpperTest(
        "coerce_datetime_pre_epoch",
        value=datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        expected="1969-12-31T23:59:59.000Z",
        msg="$toUpper should coerce pre-epoch datetime to ISO 8601",
    ),
    ToUpperTest(
        "coerce_datetime_far_future",
        value=datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        expected="9999-12-31T23:59:59.000Z",
        msg="$toUpper should coerce far-future datetime to ISO 8601",
    ),
    # Timestamp boundary values.
    ToUpperTest(
        "coerce_timestamp_max_time",
        value=Timestamp(4_294_967_295, 1),
        expected="FEB  7 06:28:15:1",
        msg="$toUpper should coerce Timestamp with max time value",
    ),
    ToUpperTest(
        "coerce_timestamp_max_inc",
        value=Timestamp(1, 4_294_967_295),
        expected="JAN  1 00:00:01:4294967295",
        msg="$toUpper should coerce Timestamp with max increment value",
    ),
    ToUpperTest(
        "coerce_timestamp_zero",
        value=Timestamp(0, 0),
        expected="JAN  1 00:00:00:0",
        msg="$toUpper should coerce zero Timestamp to epoch",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOUPPER_COERCION_TESTS))
def test_toupper_coercion(collection, test_case: ToUpperTest):
    """Test $toUpper type coercion behavior."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
