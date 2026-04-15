"""$toDate basic tests: null/missing, double/long/decimal128 conversion, string parsing,
ObjectId, Timestamp, date passthrough, invalid types, special numerics, date boundaries."""

from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    TO_TYPE_ARITY_ERROR,
)
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
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    MISSING,
    OID_MAX_SIGNED32,
    OID_MAX_UNSIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

from .utils.toDate_utils import ToDateTest

_oid_2024_01_01 = oid_from_args(2024, 1, 1, 0, 0, 0)
_oid_2024_06_15 = oid_from_args(2024, 6, 15, 12, 0, 0)
_oid_2024_12_31 = oid_from_args(2024, 12, 31, 23, 59, 59)
_oid_2018_03_27 = oid_from_args(2018, 3, 27, 4, 8, 58)
_ts_2024_01_01 = ts_from_args(2024, 1, 1, 0, 0, 0)
_ts_2024_06_15 = ts_from_args(2024, 6, 15, 12, 0, 0)
_ts_2024_12_31 = ts_from_args(2024, 12, 31, 23, 59, 59)
_ts_2021_11_23 = ts_from_args(2021, 11, 23, 17, 21, 58)


TODATE_BASIC_TESTS: list[ToDateTest] = [
    # --- Null / missing ---
    ToDateTest("null", msg="Should return null for null", value=None, expected=None),
    ToDateTest("missing", msg="Should return null for missing", value=MISSING, expected=None),
    # --- Double (ms since epoch) ---
    ToDateTest("double_zero", msg="Should handle double zero", value=0.0, expected=DATE_EPOCH),
    ToDateTest(
        "double_positive",
        msg="Should handle double positive",
        value=120000000000.5,
        expected=datetime(1973, 10, 20, 21, 20, 0),
    ),
    ToDateTest(
        "double_negative",
        msg="Should handle double negative",
        value=-120000000000.0,
        expected=datetime(1966, 3, 14, 2, 40, 0),
    ),
    ToDateTest(
        "double_one_day",
        msg="Should handle double one day",
        value=86400000.0,
        expected=datetime(1970, 1, 2, 0, 0, 0),
    ),
    ToDateTest(
        "double_fractional_truncated",
        msg="Should handle double fractional truncated",
        value=1000.9,
        expected=datetime(1970, 1, 1, 0, 0, 1),
    ),
    # --- Long (ms since epoch) ---
    ToDateTest("long_zero", msg="Should handle long zero", value=Int64(0), expected=DATE_EPOCH),
    ToDateTest(
        "long_positive",
        msg="Should handle long positive",
        value=Int64(1100000000000),
        expected=datetime(2004, 11, 9, 11, 33, 20),
    ),
    ToDateTest(
        "long_negative",
        msg="Should handle long negative",
        value=Int64(-1100000000000),
        expected=datetime(1935, 2, 22, 12, 26, 40),
    ),
    ToDateTest(
        "long_one_day",
        msg="Should handle long one day",
        value=Int64(86400000),
        expected=datetime(1970, 1, 2, 0, 0, 0),
    ),
    ToDateTest(
        "long_one_second",
        msg="Should handle long one second",
        value=Int64(1000),
        expected=datetime(1970, 1, 1, 0, 0, 1),
    ),
    ToDateTest(
        "long_one_ms",
        msg="Should handle long one ms",
        value=Int64(1),
        expected=datetime(1970, 1, 1, 0, 0, 0, 1000),
    ),
    # --- Decimal128 (ms since epoch) ---
    ToDateTest(
        "decimal_zero", msg="Should handle decimal zero", value=Decimal128("0"), expected=DATE_EPOCH
    ),
    ToDateTest(
        "decimal_positive",
        msg="Should handle decimal positive",
        value=Decimal128("1253372036000.50"),
        expected=datetime(2009, 9, 19, 14, 53, 56),
    ),
    ToDateTest(
        "decimal_negative",
        msg="Should handle decimal negative",
        value=Decimal128("-86400000"),
        expected=datetime(1969, 12, 31, 0, 0, 0),
    ),
    ToDateTest(
        "decimal_one_day",
        msg="Should handle decimal one day",
        value=Decimal128("86400000"),
        expected=datetime(1970, 1, 2, 0, 0, 0),
    ),
    # --- String ---
    ToDateTest(
        "string_date_only",
        msg="Should parse date only",
        value="2018-03-20",
        expected=datetime(2018, 3, 20, 0, 0, 0),
    ),
    ToDateTest(
        "string_datetime_z",
        msg="Should parse datetime z",
        value="2018-03-20T12:00:00Z",
        expected=datetime(2018, 3, 20, 12, 0, 0),
    ),
    ToDateTest(
        "string_datetime_offset",
        msg="Should parse datetime offset",
        value="2018-03-20T12:00:00+0500",
        expected=datetime(2018, 3, 20, 7, 0, 0),
    ),
    ToDateTest(
        "string_with_space_offset",
        msg="Should parse with space offset",
        value="2018-03-20 11:00:06 +0500",
        expected=datetime(2018, 3, 20, 6, 0, 6),
    ),
    ToDateTest(
        "string_date_2024",
        msg="Should parse date 2024",
        value="2024-01-01",
        expected=datetime(2024, 1, 1, 0, 0, 0),
    ),
    ToDateTest(
        "string_date_with_time",
        msg="Should parse date with time",
        value="2024-06-15T12:30:45Z",
        expected=datetime(2024, 6, 15, 12, 30, 45),
    ),
    # --- ObjectId (various dates) ---
    ToDateTest(
        "oid_2024_jan1",
        msg="Should handle oid 2024 jan1",
        value=_oid_2024_01_01,
        expected=datetime(2024, 1, 1, 0, 0, 0),
    ),
    ToDateTest(
        "oid_2024_jun15",
        msg="Should handle oid 2024 jun15",
        value=_oid_2024_06_15,
        expected=datetime(2024, 6, 15, 12, 0, 0),
    ),
    ToDateTest(
        "oid_2024_dec31",
        msg="Should handle oid 2024 dec31",
        value=_oid_2024_12_31,
        expected=datetime(2024, 12, 31, 23, 59, 59),
    ),
    ToDateTest(
        "oid_2018_mar27",
        msg="Should handle oid 2018 mar27",
        value=_oid_2018_03_27,
        expected=datetime(2018, 3, 27, 4, 8, 58),
    ),
    # --- Timestamp (various dates) ---
    ToDateTest(
        "ts_2024_jan1",
        msg="Should handle ts 2024 jan1",
        value=_ts_2024_01_01,
        expected=datetime(2024, 1, 1, 0, 0, 0),
    ),
    ToDateTest(
        "ts_2024_jun15",
        msg="Should handle ts 2024 jun15",
        value=_ts_2024_06_15,
        expected=datetime(2024, 6, 15, 12, 0, 0),
    ),
    ToDateTest(
        "ts_2024_dec31",
        msg="Should handle ts 2024 dec31",
        value=_ts_2024_12_31,
        expected=datetime(2024, 12, 31, 23, 59, 59),
    ),
    ToDateTest(
        "ts_2021_nov23",
        msg="Should handle ts 2021 nov23",
        value=_ts_2021_11_23,
        expected=datetime(2021, 11, 23, 17, 21, 58),
    ),
    # --- Date passthrough ---
    ToDateTest(
        "date_passthrough",
        msg="Should handle date passthrough",
        value=datetime(2024, 6, 15, 12, 0, 0),
        expected=datetime(2024, 6, 15, 12, 0, 0),
    ),
    ToDateTest("date_epoch", msg="Should handle date epoch", value=DATE_EPOCH, expected=DATE_EPOCH),
    # --- Sign handling (int32 not supported, use Long) ---
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
    # --- Invalid types ---
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
    # --- Invalid strings ---
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
    # --- Special numeric values ---
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
        expected=datetime(1969, 12, 31, 0, 0, 0),
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
        expected=datetime(2100, 12, 31, 0, 0, 0),
    ),
    ToDateTest(
        "long_far_future",
        msg="Should handle long far future",
        value=Int64(4102444800000),
        expected=datetime(2100, 1, 1, 0, 0, 0),
    ),
    ToDateTest(
        "long_pre_epoch",
        msg="Should handle long pre epoch",
        value=Int64(-86400000),
        expected=datetime(1969, 12, 31, 0, 0, 0),
    ),
    ToDateTest(
        "double_far_future",
        msg="Should handle double far future",
        value=4102444800000.0,
        expected=datetime(2100, 1, 1, 0, 0, 0),
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
        expected=datetime(1980, 1, 1, 0, 0, 0),
    ),
    ToDateTest(
        "oid_distant_future",
        msg="Should handle oid distant future",
        value=oid_from_args(2035, 6, 15, 0, 0, 0),
        expected=datetime(2035, 6, 15, 0, 0, 0),
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
        expected=datetime(2100, 6, 15, 0, 0, 0),
    ),
    # --- Additional invalid types ---
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
    # --- Negative zero ---
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
    # --- Date boundary tests ---
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
        expected=datetime(2038, 1, 19, 3, 14, 7),
    ),
    ToDateTest(
        "ts_boundary_max_u32",
        msg="Should handle ts boundary max u32",
        value=TS_MAX_UNSIGNED32,
        expected=datetime(2106, 2, 7, 6, 28, 15),
    ),
    # ObjectId boundaries
    ToDateTest(
        "oid_boundary_max_s32",
        msg="Should handle max signed 32-bit ObjectId",
        value=OID_MAX_SIGNED32,
        expected=datetime(2038, 1, 19, 3, 14, 7),
    ),
    ToDateTest(
        "oid_boundary_min_s32",
        msg="Should handle min signed 32-bit ObjectId",
        value=OID_MIN_SIGNED32,
        expected=datetime(1901, 12, 13, 20, 45, 52),
    ),
    ToDateTest(
        "oid_boundary_max_u32",
        msg="Should handle max unsigned 32-bit ObjectId",
        value=OID_MAX_UNSIGNED32,
        expected=datetime(1969, 12, 31, 23, 59, 59),
    ),
    # --- Leap year string ---
    ToDateTest(
        "string_leap_feb29",
        msg="Should parse leap feb29",
        value="2020-02-29",
        expected=datetime(2020, 2, 29, 0, 0, 0),
    ),
    ToDateTest(
        "string_leap_feb29_2024",
        msg="Should parse leap feb29 2024",
        value="2024-02-29",
        expected=datetime(2024, 2, 29, 0, 0, 0),
    ),
    ToDateTest(
        "string_leap_feb29_century_2000",
        msg="Should parse leap feb29 century 2000",
        value="2000-02-29",
        expected=datetime(2000, 2, 29, 0, 0, 0),
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


@pytest.mark.parametrize("test", TODATE_BASIC_TESTS, ids=lambda t: t.id)
def test_toDate_basic_literal(collection, test):
    """Test $toDate with literal values."""
    result = execute_expression(collection, {"$toDate": test.value})
    assert_expression_result(result, expected=test.expected, error_code=test.error_code)


@pytest.mark.parametrize(
    "test", [t for t in TODATE_BASIC_TESTS if t.id not in _LITERAL_ONLY], ids=lambda t: t.id
)
def test_toDate_basic_insert(collection, test):
    """Test $toDate from documents."""
    result = execute_expression_with_insert(
        collection, {"$toDate": "$value"}, {"value": test.value}
    )
    assert_expression_result(result, expected=test.expected, error_code=test.error_code)


# --- Array tests (literal vs insert behavior differs) ---


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
    result = execute_expression(collection, {"$toDate": [datetime(2024, 1, 1)]})
    assert_expression_result(result, expected=datetime(2024, 1, 1, 0, 0, 0))


def test_toDate_array_date_insert(collection):
    """$toDate with single-element date array from document rejects at runtime."""
    result = execute_expression_with_insert(
        collection, {"$toDate": "$value"}, {"value": [datetime(2024, 1, 1)]}
    )
    assert_expression_result(result, error_code=CONVERSION_FAILURE_ERROR)
