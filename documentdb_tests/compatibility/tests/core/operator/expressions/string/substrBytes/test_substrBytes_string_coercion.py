from __future__ import annotations

import pytest
from bson import Code, Decimal128, Int64, Timestamp

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
    INT64_MIN,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.string.substrBytes.utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [String Parameter Coercion]: non-string types for the string parameter are coerced to
# their string representation before extraction.
SUBSTRBYTES_COERCION_TESTS: list[SubstrBytesTest] = [
    # int32 and int64 coerce to decimal string representation.
    SubstrBytesTest(
        "coerce_int32",
        string=42,
        byte_index=0,
        byte_count=-1,
        expected="42",
        msg="$substrBytes should coerce int32 to string",
    ),
    SubstrBytesTest(
        "coerce_int32_negative",
        string=-42,
        byte_index=0,
        byte_count=-1,
        expected="-42",
        msg="$substrBytes should coerce negative int32 to string",
    ),
    SubstrBytesTest(
        "coerce_int32_zero",
        string=0,
        byte_index=0,
        byte_count=-1,
        expected="0",
        msg="$substrBytes should coerce int32 zero to string",
    ),
    SubstrBytesTest(
        "coerce_int64",
        string=Int64(42),
        byte_index=0,
        byte_count=-1,
        expected="42",
        msg="$substrBytes should coerce int64 to string",
    ),
    SubstrBytesTest(
        "coerce_int64_max",
        string=INT64_MAX,
        byte_index=0,
        byte_count=-1,
        expected="9223372036854775807",
        msg="$substrBytes should coerce INT64_MAX to string",
    ),
    SubstrBytesTest(
        "coerce_int64_min",
        string=INT64_MIN,
        byte_index=0,
        byte_count=-1,
        expected="-9223372036854775808",
        msg="$substrBytes should coerce INT64_MIN to string",
    ),
    # double whole numbers omit trailing .0.
    SubstrBytesTest(
        "coerce_double_whole",
        string=3.0,
        byte_index=0,
        byte_count=-1,
        expected="3",
        msg="$substrBytes should coerce whole double without trailing .0",
    ),
    SubstrBytesTest(
        "coerce_double_whole_100",
        string=100.0,
        byte_index=0,
        byte_count=-1,
        expected="100",
        msg="$substrBytes should coerce double 100 without trailing .0",
    ),
    # double with fractional part.
    SubstrBytesTest(
        "coerce_double_fractional",
        string=3.14,
        byte_index=0,
        byte_count=-1,
        expected="3.14",
        msg="$substrBytes should coerce fractional double to string",
    ),
    # double negative zero.
    SubstrBytesTest(
        "coerce_double_neg_zero",
        string=DOUBLE_NEGATIVE_ZERO,
        byte_index=0,
        byte_count=-1,
        expected="-0",
        msg="$substrBytes should coerce double negative zero",
    ),
    # double special values are lowercase.
    SubstrBytesTest(
        "coerce_double_nan",
        string=FLOAT_NAN,
        byte_index=0,
        byte_count=-1,
        expected="nan",
        msg="$substrBytes should coerce double NaN to lowercase nan",
    ),
    SubstrBytesTest(
        "coerce_double_inf",
        string=FLOAT_INFINITY,
        byte_index=0,
        byte_count=-1,
        expected="inf",
        msg="$substrBytes should coerce double Infinity to lowercase inf",
    ),
    SubstrBytesTest(
        "coerce_double_neg_inf",
        string=FLOAT_NEGATIVE_INFINITY,
        byte_index=0,
        byte_count=-1,
        expected="-inf",
        msg="$substrBytes should coerce double -Infinity to lowercase -inf",
    ),
    # double uses scientific notation for large and small magnitudes.
    SubstrBytesTest(
        "coerce_double_sci_large",
        string=1e6,
        byte_index=0,
        byte_count=-1,
        expected="1e+06",
        msg="$substrBytes should coerce large double to scientific notation",
    ),
    SubstrBytesTest(
        "coerce_double_sci_small",
        string=1e-10,
        byte_index=0,
        byte_count=-1,
        expected="1e-10",
        msg="$substrBytes should coerce small double to scientific notation",
    ),
    SubstrBytesTest(
        "coerce_double_precision_limit",
        string=float(DOUBLE_MAX_SAFE_INTEGER),
        byte_index=0,
        byte_count=-1,
        expected="9.0072e+15",
        msg="$substrBytes should coerce double at precision limit",
    ),
    # Decimal128 preserves exact string representation including trailing zeros.
    SubstrBytesTest(
        "coerce_decimal_trailing",
        string=DECIMAL128_TRAILING_ZERO,
        byte_index=0,
        byte_count=-1,
        expected="1.0",
        msg="$substrBytes should preserve Decimal128 trailing zeros",
    ),
    SubstrBytesTest(
        "coerce_decimal_neg_zero",
        string=Decimal128("-0.0"),
        byte_index=0,
        byte_count=-1,
        expected="-0.0",
        msg="$substrBytes should preserve Decimal128 negative zero",
    ),
    SubstrBytesTest(
        "coerce_decimal_sci",
        string=Decimal128("1.23E+10"),
        byte_index=0,
        byte_count=-1,
        expected="1.23E+10",
        msg="$substrBytes should preserve Decimal128 scientific notation",
    ),
    # Decimal128 preserves full 34-digit precision.
    SubstrBytesTest(
        "coerce_decimal_34_digits",
        string=Decimal128("1234567890123456789012345678901234"),
        byte_index=0,
        byte_count=-1,
        expected="1234567890123456789012345678901234",
        msg="$substrBytes should preserve Decimal128 34-digit precision",
    ),
    SubstrBytesTest(
        "coerce_decimal_min_positive",
        string=DECIMAL128_MIN_POSITIVE,
        byte_index=0,
        byte_count=-1,
        expected="1E-6176",
        msg="$substrBytes should coerce Decimal128 minimum positive value",
    ),
    SubstrBytesTest(
        "coerce_decimal_max_negative",
        string=DECIMAL128_MAX_NEGATIVE,
        byte_index=0,
        byte_count=-1,
        expected="-1E-6176",
        msg="$substrBytes should coerce Decimal128 maximum negative value",
    ),
    # Decimal128 special values are capitalized (unlike double's lowercase).
    SubstrBytesTest(
        "coerce_decimal_nan",
        string=Decimal128("NaN"),
        byte_index=0,
        byte_count=-1,
        expected="NaN",
        msg="$substrBytes should coerce Decimal128 NaN with capitalization",
    ),
    SubstrBytesTest(
        "coerce_decimal_infinity",
        string=DECIMAL128_INFINITY,
        byte_index=0,
        byte_count=-1,
        expected="Infinity",
        msg="$substrBytes should coerce Decimal128 Infinity with capitalization",
    ),
    SubstrBytesTest(
        "coerce_decimal_neg_infinity",
        string=DECIMAL128_NEGATIVE_INFINITY,
        byte_index=0,
        byte_count=-1,
        expected="-Infinity",
        msg="$substrBytes should coerce Decimal128 -Infinity with capitalization",
    ),
    # datetime coerces to ISO 8601 format.
    SubstrBytesTest(
        "coerce_datetime",
        string={"$toDate": "2024-01-15T10:30:45.123Z"},
        byte_index=0,
        byte_count=-1,
        expected="2024-01-15T10:30:45.123Z",
        msg="$substrBytes should coerce datetime to ISO 8601",
    ),
    SubstrBytesTest(
        "coerce_datetime_pre_epoch",
        string={"$toDate": "1969-07-20T20:17:40.000Z"},
        byte_index=0,
        byte_count=-1,
        expected="1969-07-20T20:17:40.000Z",
        msg="$substrBytes should coerce pre-epoch datetime to ISO 8601",
    ),
    # Timestamp coerces to "Mon DD HH:MM:SS:increment" with double-space padding for single-digit
    # days.
    SubstrBytesTest(
        "coerce_timestamp_single_digit_day",
        string=Timestamp(1704067200, 1),
        byte_index=0,
        byte_count=-1,
        expected="Jan  1 00:00:00:1",
        msg="$substrBytes should coerce Timestamp with single-digit day",
    ),
    SubstrBytesTest(
        "coerce_timestamp_double_digit_day",
        string=Timestamp(1721500800, 1),
        byte_index=0,
        byte_count=-1,
        expected="Jul 20 18:40:00:1",
        msg="$substrBytes should coerce Timestamp with double-digit day",
    ),
    SubstrBytesTest(
        "coerce_timestamp_increment",
        string=Timestamp(1704067200, 42),
        byte_index=0,
        byte_count=-1,
        expected="Jan  1 00:00:00:42",
        msg="$substrBytes should coerce Timestamp preserving increment",
    ),
    # Code (without scope) coerces to its code string.
    SubstrBytesTest(
        "coerce_code",
        string=Code("function() { return 1; }"),
        byte_index=0,
        byte_count=-1,
        expected="function() { return 1; }",
        msg="$substrBytes should coerce Code to its code string",
    ),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_COERCION_TESTS))
def test_substrbytes_string_coercion(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes string coercion cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
