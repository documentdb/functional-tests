"""$toDate basic tests: null/missing, double/long/decimal128 conversion, string parsing,
ObjectId, Timestamp, date passthrough, invalid types, special numerics, date boundaries."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, Regex
from bson.errors import InvalidBSON

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertExceptionType
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    TO_TYPE_ARITY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DATE_MS_BEFORE_EPOCH,
    DATE_MS_EPOCH,
    DATE_YEAR_1900,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
    MISSING,
    OID_MAX_SIGNED32,
    OID_MAX_UNSIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

from .utils.toDate_utils import _DOC_EXPR_FORMS, _EXPR_FORMS, ToDateTest

_oid_2024_01_01 = oid_from_args(2024, 1, 1, 0, 0, 0)
_oid_2024_06_15 = oid_from_args(2024, 6, 15, 12, 0, 0)
_oid_2024_12_31 = oid_from_args(2024, 12, 31, 23, 59, 59)
_oid_2018_03_27 = oid_from_args(2018, 3, 27, 4, 8, 58)
_ts_2024_01_01 = ts_from_args(2024, 1, 1, 0, 0, 0)
_ts_2024_06_15 = ts_from_args(2024, 6, 15, 12, 0, 0)
_ts_2024_12_31 = ts_from_args(2024, 12, 31, 23, 59, 59)
_ts_2021_11_23 = ts_from_args(2021, 11, 23, 17, 21, 58)


# Property [Basic Conversion]: $toDate converts supported BSON types to dates,
# returns null for null/missing, and rejects unsupported types.
TODATE_BASIC_TESTS: list[ToDateTest] = [
    # Null / missing.
    ToDateTest("null", msg="Should return null for null", value=None, expected=None),
    ToDateTest("missing", msg="Should return null for missing", value=MISSING, expected=None),
    # Double (ms since epoch).
    ToDateTest(
        "double_zero", msg="Should handle double zero", value=DOUBLE_ZERO, expected=DATE_EPOCH
    ),
    ToDateTest(
        "double_positive",
        msg="Should handle double positive",
        value=120000000000.5,
        expected=datetime(1973, 10, 20, 21, 20, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "double_negative",
        msg="Should handle double negative",
        value=-120000000000.0,
        expected=datetime(1966, 3, 14, 2, 40, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "double_one_day",
        msg="Should handle double one day",
        value=86400000.0,
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "double_fractional_truncated",
        msg="Should handle double fractional truncated",
        value=1000.9,
        expected=datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
    ),
    # Long (ms since epoch).
    ToDateTest("long_zero", msg="Should handle long zero", value=INT64_ZERO, expected=DATE_EPOCH),
    ToDateTest(
        "long_positive",
        msg="Should handle long positive",
        value=Int64(1100000000000),
        expected=datetime(2004, 11, 9, 11, 33, 20, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "long_negative",
        msg="Should handle long negative",
        value=Int64(-1100000000000),
        expected=datetime(1935, 2, 22, 12, 26, 40, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "long_one_day",
        msg="Should handle long one day",
        value=Int64(86400000),
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "long_one_second",
        msg="Should handle long one second",
        value=Int64(1000),
        expected=datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "long_one_ms",
        msg="Should handle long one ms",
        value=Int64(1),
        expected=datetime(1970, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
    ),
    # Decimal128 (ms since epoch).
    ToDateTest(
        "decimal_zero", msg="Should handle decimal zero", value=DECIMAL128_ZERO, expected=DATE_EPOCH
    ),
    ToDateTest(
        "decimal_positive",
        msg="Should handle decimal positive",
        value=Decimal128("1253372036000.50"),
        expected=datetime(2009, 9, 19, 14, 53, 56, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "decimal_negative",
        msg="Should handle decimal negative",
        value=Decimal128("-86400000"),
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "decimal_one_day",
        msg="Should handle decimal one day",
        value=Decimal128("86400000"),
        expected=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
    ),
    # String.
    ToDateTest(
        "string_date_only",
        msg="Should parse date only",
        value="2018-03-20",
        expected=datetime(2018, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_datetime_z",
        msg="Should parse datetime z",
        value="2018-03-20T12:00:00Z",
        expected=datetime(2018, 3, 20, 12, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_datetime_offset",
        msg="Should parse datetime offset",
        value="2018-03-20T12:00:00+0500",
        expected=datetime(2018, 3, 20, 7, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_date_2024",
        msg="Should parse date 2024",
        value="2024-01-01",
        expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_date_with_time",
        msg="Should parse date with time",
        value="2024-06-15T12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_datetime_no_tz",
        msg="Should parse datetime without timezone",
        value="2024-06-15T12:30:45",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    # String whitespace trimming.
    ToDateTest(
        "string_leading_space",
        msg="Should trim leading space",
        value=" 2024-06-15T12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_trailing_space",
        msg="Should trim trailing space",
        value="2024-06-15T12:30:45Z ",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_leading_tab",
        msg="Should trim leading tab",
        value="\t2024-06-15T12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_trailing_tab",
        msg="Should trim trailing tab",
        value="2024-06-15T12:30:45Z\t",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_leading_newline",
        msg="Should trim leading newline",
        value="\n2024-06-15T12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_trailing_newline",
        msg="Should trim trailing newline",
        value="2024-06-15T12:30:45Z\n",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_leading_null_byte",
        msg="Should trim leading null byte",
        value="\x002024-06-15T12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_trailing_null_byte",
        msg="Should trim trailing null byte",
        value="2024-06-15T12:30:45Z\x00",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_leading_nbsp",
        msg="Should trim leading NBSP",
        value="\u00a02024-06-15T12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_trailing_nbsp",
        msg="Should trim trailing NBSP",
        value="2024-06-15T12:30:45Z\u00a0",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_tab_separator",
        msg="Should accept tab as date/time separator",
        value="2024-06-15\t12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_multiple_space_separator",
        msg="Should accept multiple spaces as date/time separator",
        value="2024-06-15  12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_space_before_tz",
        msg="Should accept space before timezone designator",
        value="2024-06-15T12:30:45 Z",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_space_separator_with_offset",
        msg="Should parse space-separated date/time with space before numeric offset",
        value="2018-03-20 11:00:06 +0500",
        expected=datetime(2018, 3, 20, 6, 0, 6, tzinfo=timezone.utc),
    ),
    # Timezone offset formats.
    ToDateTest(
        "string_tz_plus_colon",
        msg="Should parse +HH:MM timezone offset",
        value="2024-06-15T12:30:45+05:00",
        expected=datetime(2024, 6, 15, 7, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_tz_plus_compact",
        msg="Should parse +HHMM timezone offset",
        value="2024-06-15T12:30:45+0500",
        expected=datetime(2024, 6, 15, 7, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_tz_minus_zero_colon",
        msg="Should parse -00:00 timezone offset",
        value="2024-06-15T12:30:45-00:00",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_tz_plus_zero_compact",
        msg="Should parse +0000 timezone offset",
        value="2024-06-15T12:30:45+0000",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_tz_plus_zero_short",
        msg="Should parse +HH shorthand timezone offset",
        value="2024-06-15T12:30:45+00",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_tz_minus_colon",
        msg="Should parse -HH:MM timezone offset",
        value="2024-06-15T12:30:45-05:30",
        expected=datetime(2024, 6, 15, 18, 0, 45, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_tz_minus_compact",
        msg="Should parse -HHMM timezone offset",
        value="2024-06-15T12:30:45-0530",
        expected=datetime(2024, 6, 15, 18, 0, 45, tzinfo=timezone.utc),
    ),
    # ObjectId (various dates).
    ToDateTest(
        "oid_2024_jan1",
        msg="Should handle oid 2024 jan1",
        value=_oid_2024_01_01,
        expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "oid_2024_jun15",
        msg="Should handle oid 2024 jun15",
        value=_oid_2024_06_15,
        expected=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "oid_2024_dec31",
        msg="Should handle oid 2024 dec31",
        value=_oid_2024_12_31,
        expected=datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "oid_2018_mar27",
        msg="Should handle oid 2018 mar27",
        value=_oid_2018_03_27,
        expected=datetime(2018, 3, 27, 4, 8, 58, tzinfo=timezone.utc),
    ),
    # Timestamp (various dates).
    ToDateTest(
        "ts_2024_jan1",
        msg="Should handle ts 2024 jan1",
        value=_ts_2024_01_01,
        expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "ts_2024_jun15",
        msg="Should handle ts 2024 jun15",
        value=_ts_2024_06_15,
        expected=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "ts_2024_dec31",
        msg="Should handle ts 2024 dec31",
        value=_ts_2024_12_31,
        expected=datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "ts_2021_nov23",
        msg="Should handle ts 2021 nov23",
        value=_ts_2021_11_23,
        expected=datetime(2021, 11, 23, 17, 21, 58, tzinfo=timezone.utc),
    ),
    # Date passthrough.
    ToDateTest(
        "date_passthrough",
        msg="Should handle date passthrough",
        value=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        expected=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest("date_epoch", msg="Should handle date epoch", value=DATE_EPOCH, expected=DATE_EPOCH),
    # Sign handling (int32 not supported, use Long).
    ToDateTest(
        "int_zero_error",
        msg="Should reject int zero",
        value=0,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "int_positive_error",
        msg="Should reject int positive",
        value=86400000,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "int_negative_error",
        msg="Should reject int negative",
        value=-86400000,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # Invalid types.
    ToDateTest(
        "bool_true", msg="Should reject bool true", value=True, error_code=CONVERSION_FAILURE_ERROR
    ),
    ToDateTest(
        "bool_false",
        msg="Should reject bool false",
        value=False,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "object", msg="Should reject object", value={"a": 1}, error_code=CONVERSION_FAILURE_ERROR
    ),
    # Invalid strings.
    ToDateTest(
        "string_friday",
        msg="Should parse friday",
        value="Friday",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "string_not_a_date",
        msg="Should parse not a date",
        value="not-a-date",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "string_empty", msg="Should parse empty", value="", error_code=CONVERSION_FAILURE_ERROR
    ),
    ToDateTest(
        "string_year_only",
        msg="Should reject year-only string",
        value="2024",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "string_space_in_date",
        msg="Should reject space within date portion",
        value="2024 -06-15T12:30:45Z",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "string_space_in_time",
        msg="Should reject space within time portion",
        value="2024-06-15T12: 30:45Z",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # Special numeric values.
    ToDateTest(
        "nan_double",
        msg="Should reject nan double",
        value=FLOAT_NAN,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "inf_double",
        msg="Should reject inf double",
        value=FLOAT_INFINITY,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "neg_inf_double",
        msg="Should reject neg inf double",
        value=FLOAT_NEGATIVE_INFINITY,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "nan_decimal",
        msg="Should reject nan decimal",
        value=DECIMAL128_NAN,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "inf_decimal",
        msg="Should reject inf decimal",
        value=DECIMAL128_INFINITY,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "neg_inf_decimal",
        msg="Should reject neg inf decimal",
        value=DECIMAL128_NEGATIVE_INFINITY,
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # Pre-epoch and distant dates
    ToDateTest(
        "string_pre_epoch",
        msg="Should parse pre epoch",
        value="1969-12-31",
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_distant_past",
        msg="Should parse distant past",
        value="1900-01-01",
        expected=DATE_YEAR_1900,
    ),
    ToDateTest(
        "string_distant_future",
        msg="Should parse distant future",
        value="2100-12-31",
        expected=datetime(2100, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "long_far_future",
        msg="Should handle long far future",
        value=Int64(4102444800000),
        expected=datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "long_pre_epoch",
        msg="Should handle long pre epoch",
        value=Int64(-86400000),
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "double_far_future",
        msg="Should handle double far future",
        value=4102444800000.0,
        expected=datetime(2100, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    ),
    # OID/TS at distant dates
    ToDateTest(
        "oid_epoch",
        msg="Should handle oid epoch",
        value=oid_from_args(1970, 1, 1, 0, 0, 0),
        expected=DATE_EPOCH,
    ),
    ToDateTest(
        "oid_1980",
        msg="Should handle oid 1980",
        value=oid_from_args(1980, 1, 1, 0, 0, 0),
        expected=datetime(1980, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "oid_distant_future",
        msg="Should handle oid distant future",
        value=oid_from_args(2035, 6, 15, 0, 0, 0),
        expected=datetime(2035, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "ts_epoch",
        msg="Should handle ts epoch",
        value=ts_from_args(1970, 1, 1, 0, 0, 0),
        expected=DATE_EPOCH,
    ),
    ToDateTest(
        "ts_distant_future",
        msg="Should handle ts distant future",
        value=ts_from_args(2100, 6, 15, 0, 0, 0),
        expected=datetime(2100, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
    ),
    # Additional invalid types.
    ToDateTest(
        "regex", msg="Should reject regex", value=Regex(".*"), error_code=CONVERSION_FAILURE_ERROR
    ),
    ToDateTest(
        "minkey", msg="Should reject minkey", value=MinKey(), error_code=CONVERSION_FAILURE_ERROR
    ),
    ToDateTest(
        "maxkey", msg="Should reject maxkey", value=MaxKey(), error_code=CONVERSION_FAILURE_ERROR
    ),
    ToDateTest(
        "bindata",
        msg="Should reject bindata",
        value=Binary(b""),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "javascript",
        msg="Should reject javascript",
        value=Code("function(){}"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "javascript_with_scope",
        msg="Should reject javascript with scope",
        value=Code("function(){}", {}),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # Negative zero.
    ToDateTest(
        "double_neg_zero",
        msg="Should handle double neg zero",
        value=DOUBLE_NEGATIVE_ZERO,
        expected=DATE_EPOCH,
    ),
    ToDateTest(
        "decimal_neg_zero",
        msg="Should handle decimal neg zero",
        value=DECIMAL128_NEGATIVE_ZERO,
        expected=DATE_EPOCH,
    ),
    # Date boundary tests.
    ToDateTest(
        "date_passthrough_epoch_ms",
        msg="Should handle date passthrough epoch ms",
        value=DATE_MS_EPOCH,
        expected=DATE_EPOCH,
    ),
    ToDateTest(
        "date_passthrough_before_epoch_ms",
        msg="Should handle date passthrough before epoch ms",
        value=DATE_MS_BEFORE_EPOCH,
        expected=DATE_BEFORE_EPOCH,
    ),
    ToDateTest(
        "ts_boundary_max_s32",
        msg="Should handle ts boundary max s32",
        value=TS_MAX_SIGNED32,
        expected=datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "ts_boundary_max_u32",
        msg="Should handle ts boundary max u32",
        value=TS_MAX_UNSIGNED32,
        expected=datetime(2106, 2, 7, 6, 28, 15, tzinfo=timezone.utc),
    ),
    # ObjectId boundaries
    ToDateTest(
        "oid_boundary_max_s32",
        msg="Should handle max signed 32-bit ObjectId",
        value=OID_MAX_SIGNED32,
        expected=datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "oid_boundary_min_s32",
        msg="Should handle min signed 32-bit ObjectId",
        value=OID_MIN_SIGNED32,
        expected=datetime(1901, 12, 13, 20, 45, 52, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "oid_boundary_max_u32",
        msg="Should handle max unsigned 32-bit ObjectId",
        value=OID_MAX_UNSIGNED32,
        expected=datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    ),
    # Year boundary tests.
    ToDateTest(
        "string_year_0001",
        msg="Should parse earliest representable year string",
        value="0001-01-01T00:00:00Z",
        expected=datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_year_9999_end",
        msg="Should parse last millisecond of year 9999",
        value="9999-12-31T23:59:59.999Z",
        expected=datetime(9999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_year_10000",
        msg="Should reject year 10000 string",
        value="10000-01-01T00:00:00Z",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "long_year_9999_end",
        msg="Should handle last millisecond of year 9999 from Int64",
        value=Int64(253402300799999),
        expected=datetime(9999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc),
    ),
    # Year strings with more than 4 digits should be rejected. Testing revealed
    # that some implementations silently misparse these depending on whether the
    # first 4 digits exceed a 2-digit year cutoff (2059). Both sides of that
    # boundary are tested, along with longer digit sequences.
    ToDateTest(
        "string_year_5_digits_low_prefix",
        msg="Should reject 5-digit year string with prefix <= 2059",
        value="20599-01-01T00:00:00Z",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "string_year_5_digits_high_prefix",
        msg="Should reject 5-digit year string with prefix > 2059",
        value="20609-01-01T00:00:00Z",
        error_code=CONVERSION_FAILURE_ERROR,
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB silently misparses multi-digit year strings instead of rejecting",
                raises=AssertionError,
            ),
        ),
    ),
    ToDateTest(
        "string_year_5_digits_max",
        msg="Should reject 5-digit year string starting with 9999",
        value="99999-01-01T00:00:00Z",
        error_code=CONVERSION_FAILURE_ERROR,
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB silently misparses multi-digit year strings instead of rejecting",
                raises=AssertionError,
            ),
        ),
    ),
    ToDateTest(
        "string_year_6_digits",
        msg="Should reject 6-digit year string",
        value="199990-01-01T00:00:00Z",
        error_code=CONVERSION_FAILURE_ERROR,
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB silently misparses multi-digit year strings instead of rejecting",
                raises=AssertionError,
            ),
        ),
    ),
    ToDateTest(
        "string_year_50_digits",
        msg="Should reject year string far exceeding numeric limits",
        value="9" * 49 + "1-01-01T00:00:00Z",
        error_code=CONVERSION_FAILURE_ERROR,
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB silently misparses multi-digit year strings instead of rejecting",
                raises=AssertionError,
            ),
        ),
    ),
    # Leap year string.
    ToDateTest(
        "string_leap_feb29",
        msg="Should parse leap feb29",
        value="2020-02-29",
        expected=datetime(2020, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_leap_feb29_2024",
        msg="Should parse leap feb29 2024",
        value="2024-02-29",
        expected=datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_leap_feb29_century_2000",
        msg="Should parse leap feb29 century 2000",
        value="2000-02-29",
        expected=datetime(2000, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
    ),
    ToDateTest(
        "string_non_leap_feb29",
        msg="Should reject non leap feb29",
        value="2019-02-29",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDateTest(
        "string_non_leap_century_1900",
        msg="Should reject 1900 non-leap century feb29",
        value="1900-02-29",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

_LITERAL_ONLY = {t.id for t in TODATE_BASIC_TESTS if t.value is MISSING}


@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
@pytest.mark.parametrize("test", pytest_params(TODATE_BASIC_TESTS))
def test_toDate_basic_literal(collection, test, expr_fn):
    """Test $toDate with literal values."""
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(result, expected=test.expected, error_code=test.error_code)


@pytest.mark.parametrize("expr_fn", _DOC_EXPR_FORMS)
@pytest.mark.parametrize(
    "test", pytest_params([t for t in TODATE_BASIC_TESTS if t.id not in _LITERAL_ONLY])
)
def test_toDate_basic_insert(collection, test, expr_fn):
    """Test $toDate from documents."""
    result = execute_expression_with_insert(collection, expr_fn("$value"), {"value": test.value})
    assert_expression_result(result, expected=test.expected, error_code=test.error_code)


# Array tests (literal vs insert behavior differs).


def test_toDate_array_literal(collection):
    """$toDate with array literal rejects at parse time (error 50723)."""
    result = execute_expression(collection, {"$toDate": [1, 2]})
    assert_expression_result(result, error_code=TO_TYPE_ARITY_ERROR)


def test_toDate_array_insert(collection):
    """$toDate with array from document rejects at runtime (error 241)."""
    result = execute_expression_with_insert(collection, {"$toDate": "$value"}, {"value": [1, 2]})
    assert_expression_result(result, error_code=CONVERSION_FAILURE_ERROR)


def test_toDate_array_date_literal(collection):
    """$toDate with single-element date array literal unwraps at parse time."""
    result = execute_expression(
        collection, {"$toDate": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}
    )
    assert_expression_result(result, expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc))


def test_toDate_array_date_insert(collection):
    """$toDate with single-element date array from document rejects at runtime."""
    result = execute_expression_with_insert(
        collection, {"$toDate": "$value"}, {"value": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}
    )
    assert_expression_result(result, error_code=CONVERSION_FAILURE_ERROR)


# Out-of-Python-range year boundary tests.
# Python's datetime cannot represent years outside 1-9999, so we use $year
# to extract and verify the year without decoding the Date client-side.

# Property [Out-of-Range Year]: $toDate produces correct dates for years
# outside Python's 1-9999 range, verified via $year extraction.
TODATE_OUT_OF_RANGE_YEAR_TESTS: list[ToDateTest] = [
    ToDateTest(
        "long_year_negative",
        msg="$toDate should produce year -1 from Int64",
        value=Int64(-62198755200000),
        expected=-1,
    ),
    ToDateTest(
        "long_year_0",
        msg="$toDate should produce year 0 from Int64",
        value=Int64(-62167219200000),
        expected=0,
    ),
    ToDateTest(
        "long_year_10000",
        msg="$toDate should produce year 10000 from Int64",
        value=Int64(253402300800000),
        expected=10000,
    ),
    ToDateTest(
        "string_year_negative",
        msg="$toDate should produce year -1 from string",
        value="-0001-01-01T00:00:00Z",
        expected=-1,
    ),
    ToDateTest(
        "string_year_0",
        msg="$toDate should produce year 0 from string",
        value="0000-01-01T00:00:00Z",
        expected=0,
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODATE_OUT_OF_RANGE_YEAR_TESTS))
def test_toDate_out_of_range_year(collection, test):
    """Test $toDate creates correct Date for out-of-Python-range years."""
    result = execute_expression(collection, {"$year": {"$toDate": test.value}})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


@pytest.mark.parametrize(
    "label, ms",
    [
        ("year_negative", Int64(-62198755200000)),
        ("year_0", Int64(-62167219200000)),
        ("year_10000", Int64(253402300800000)),
    ],
)
def test_toDate_out_of_range_year_driver_rejects(collection, label, ms):
    """Test that the BSON driver raises InvalidBSON when decoding out-of-range dates."""
    result = execute_expression(collection, {"$toDate": ms})
    assertExceptionType(
        result,
        InvalidBSON,
        msg=f"BSON driver should raise InvalidBSON when decoding {label} date",
    )
