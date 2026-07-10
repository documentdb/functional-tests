"""$toDouble basic tests: null/missing, boolean, integer, double identity,
decimal128, string, hex float, datetime, binary, and unsupported type errors."""

import struct
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccessNaN
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_ZERO,
    MISSING,
)

from .utils.toDouble_utils import _EXPR_FORMS, ToDoubleTest

# Pre-computed binary values: 4-byte little-endian float32.
_f32_zero = Binary(struct.pack("<f", 0.0))
_f32_one = Binary(struct.pack("<f", 1.0))
_f32_neg_one = Binary(struct.pack("<f", -1.0))
_f32_two = Binary(struct.pack("<f", 2.0))

# Pre-computed binary values: 8-byte little-endian float64.
_f64_zero = Binary(struct.pack("<d", 0.0))
_f64_one = Binary(struct.pack("<d", 1.0))
_f64_neg_one = Binary(struct.pack("<d", -1.0))
_f64_1_5 = Binary(struct.pack("<d", 1.5))


TODOUBLE_BASIC_TESTS: list[ToDoubleTest] = [
    # Null / missing.
    ToDoubleTest("null", msg="Should return null for null", value=None, expected=None),
    ToDoubleTest("missing", msg="Should return null for missing", value=MISSING, expected=None),
    # Boolean.
    ToDoubleTest("bool_true", msg="True converts to 1.0", value=True, expected=1.0),
    ToDoubleTest(
        "bool_false", msg="False converts to positive 0.0", value=False, expected=DOUBLE_ZERO
    ),
    # int32.
    ToDoubleTest("int32_zero", msg="int32 zero converts to 0.0", value=INT32_ZERO, expected=0.0),
    ToDoubleTest("int32_one", msg="int32 1 converts exactly to 1.0", value=1, expected=1.0),
    ToDoubleTest("int32_neg_one", msg="int32 -1 converts exactly to -1.0", value=-1, expected=-1.0),
    ToDoubleTest(
        "int32_max", msg="int32 max converts exactly", value=INT32_MAX, expected=2147483647.0
    ),
    ToDoubleTest(
        "int32_min", msg="int32 min converts exactly", value=INT32_MIN, expected=-2147483648.0
    ),
    # int64.
    ToDoubleTest("int64_zero", msg="int64 zero converts to 0.0", value=INT64_ZERO, expected=0.0),
    ToDoubleTest("int64_one", msg="int64 1 converts to 1.0", value=Int64(1), expected=1.0),
    ToDoubleTest(
        "int64_safe_max",
        msg="int64 at 2^53 (max safe integer) converts exactly",
        value=Int64(9007199254740992),
        expected=9007199254740992.0,
    ),
    ToDoubleTest(
        "int64_above_safe",
        msg="int64 above 2^53 loses the last bit of precision",
        value=Int64(9007199254740993),
        expected=9007199254740992.0,
    ),
    ToDoubleTest(
        "int64_neg_one",
        msg="int64 -1 converts to -1.0",
        value=Int64(-1),
        expected=-1.0,
    ),
    ToDoubleTest(
        "int64_max",
        msg="int64 max converts with precision loss",
        value=INT64_MAX,
        expected=DOUBLE_FROM_INT64_MAX,
    ),
    ToDoubleTest(
        "int64_max_minus_one",
        msg="int64 max-1 rounds to the same double as int64 max",
        value=INT64_MAX_MINUS_1,
        expected=DOUBLE_FROM_INT64_MAX,
    ),
    ToDoubleTest(
        "int64_min",
        msg="int64 min converts to -2^63 representation",
        value=INT64_MIN,
        expected=-9.223372036854776e18,
    ),
    # Double identity (passthrough).
    ToDoubleTest(
        "double_zero", msg="0.0 passes through unchanged", value=DOUBLE_ZERO, expected=0.0
    ),
    ToDoubleTest(
        "double_neg_zero",
        msg="-0.0 passes through preserving sign",
        value=DOUBLE_NEGATIVE_ZERO,
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
    ToDoubleTest(
        "double_inf",
        msg="+Inf passes through unchanged",
        value=FLOAT_INFINITY,
        expected=FLOAT_INFINITY,
    ),
    ToDoubleTest(
        "double_neg_inf",
        msg="-Inf passes through unchanged",
        value=FLOAT_NEGATIVE_INFINITY,
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ToDoubleTest("double_one", msg="1.0 passes through unchanged", value=1.0, expected=1.0),
    ToDoubleTest(
        "double_pi",
        msg="pi passes through unchanged",
        value=3.141592653589793,
        expected=3.141592653589793,
    ),
    ToDoubleTest(
        "double_large",
        msg="Large double passes through unchanged",
        value=1.7976931348623157e308,
        expected=1.7976931348623157e308,
    ),
    ToDoubleTest(
        "double_subnormal",
        msg="Minimum positive subnormal double passes through unchanged",
        value=DOUBLE_MIN_SUBNORMAL,
        expected=DOUBLE_MIN_SUBNORMAL,
    ),
    ToDoubleTest(
        "double_neg_subnormal",
        msg="Minimum negative subnormal double passes through unchanged",
        value=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
        expected=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    ),
    # Decimal128.
    ToDoubleTest(
        "dec128_zero", msg="Decimal128 zero converts to 0.0", value=DECIMAL128_ZERO, expected=0.0
    ),
    ToDoubleTest(
        "dec128_neg_zero",
        msg="Decimal128 -0 converts to -0.0 preserving sign",
        value=DECIMAL128_NEGATIVE_ZERO,
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
    ToDoubleTest(
        "dec128_inf",
        msg="Decimal128 Infinity converts to +Inf",
        value=DECIMAL128_INFINITY,
        expected=FLOAT_INFINITY,
    ),
    ToDoubleTest(
        "dec128_neg_inf",
        msg="Decimal128 -Infinity converts to -Inf",
        value=DECIMAL128_NEGATIVE_INFINITY,
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ToDoubleTest(
        "dec128_one", msg="Decimal128 1 converts to 1.0", value=Decimal128("1"), expected=1.0
    ),
    ToDoubleTest(
        "dec128_trailing_zero",
        msg="Decimal128 trailing zero normalizes correctly",
        value=Decimal128("1.0"),
        expected=1.0,
    ),
    ToDoubleTest(
        "dec128_many_trailing_zeros",
        msg="Decimal128 with many trailing zeros normalizes correctly",
        value=Decimal128("1.00000000000000000000000000000000"),
        expected=1.0,
    ),
    ToDoubleTest(
        "dec128_neg",
        msg="Decimal128 negative value converts correctly",
        value=Decimal128("-1.5"),
        expected=-1.5,
    ),
    ToDoubleTest(
        "dec128_overflow",
        msg="Decimal128 value exceeding double max is a conversion failure",
        value=Decimal128("9.999999999999999999999999999999999E+6144"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "dec128_neg_overflow",
        msg="Decimal128 most-negative value exceeding double range is a conversion failure",
        value=Decimal128("-9.999999999999999999999999999999999E+6144"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "dec128_underflow",
        msg="Decimal128 too small for double underflows to 0.0",
        value=Decimal128("1E-6176"),
        expected=0.0,
    ),
    # String: valid numeric conversions.
    ToDoubleTest("str_zero", msg="'0' converts to 0.0", value="0", expected=0.0),
    ToDoubleTest("str_one", msg="'1' converts to 1.0", value="1", expected=1.0),
    ToDoubleTest("str_neg_one", msg="'-1' converts to -1.0", value="-1", expected=-1.0),
    ToDoubleTest("str_plus_one", msg="'+1' converts to 1.0", value="+1", expected=1.0),
    ToDoubleTest("str_decimal", msg="'1.5' converts to 1.5", value="1.5", expected=1.5),
    ToDoubleTest("str_dot_five", msg="'.5' converts to 0.5", value=".5", expected=0.5),
    ToDoubleTest(
        "str_neg_zero", msg="'-0' converts to -0.0", value="-0", expected=DOUBLE_NEGATIVE_ZERO
    ),
    ToDoubleTest(
        "str_sci_pos", msg="'1e10' (scientific) converts correctly", value="1e10", expected=1e10
    ),
    ToDoubleTest(
        "str_sci_neg_exp",
        msg="'1.5e-3' (scientific negative exponent) converts correctly",
        value="1.5e-3",
        expected=1.5e-3,
    ),
    ToDoubleTest(
        "str_sci_upper", msg="'1E10' (uppercase E) converts correctly", value="1E10", expected=1e10
    ),
    ToDoubleTest(
        "str_inf", msg="'Infinity' converts to +Inf", value="Infinity", expected=FLOAT_INFINITY
    ),
    ToDoubleTest(
        "str_neg_inf",
        msg="'-Infinity' converts to -Inf",
        value="-Infinity",
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ToDoubleTest(
        "str_plus_inf",
        msg="'+Infinity' converts to +Inf",
        value="+Infinity",
        expected=FLOAT_INFINITY,
    ),
    ToDoubleTest(
        "str_inf_short", msg="'inf' converts to +Inf", value="inf", expected=FLOAT_INFINITY
    ),
    ToDoubleTest(
        "str_neg_inf_short",
        msg="'-inf' converts to -Inf",
        value="-inf",
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    # String: hex float.
    ToDoubleTest("str_hex_zero", msg="'0x0p0' converts to 0.0", value="0x0p0", expected=0.0),
    ToDoubleTest("str_hex_one", msg="'0x1p0' converts to 1.0", value="0x1p0", expected=1.0),
    ToDoubleTest("str_hex_two", msg="'0x1p1' converts to 2.0", value="0x1p1", expected=2.0),
    ToDoubleTest("str_hex_half", msg="'0x1p-1' converts to 0.5", value="0x1p-1", expected=0.5),
    ToDoubleTest("str_hex_frac", msg="'0x1.8p1' converts to 3.0", value="0x1.8p1", expected=3.0),
    ToDoubleTest("str_hex_neg", msg="'-0x1p0' converts to -1.0", value="-0x1p0", expected=-1.0),
    ToDoubleTest("str_hex_plus", msg="'+0x1p0' converts to 1.0", value="+0x1p0", expected=1.0),
    ToDoubleTest(
        "str_hex_upper", msg="'0X1P0' (uppercase) converts to 1.0", value="0X1P0", expected=1.0
    ),
    ToDoubleTest("str_hex_ff", msg="'0xffp0' converts to 255.0", value="0xffp0", expected=255.0),
    ToDoubleTest(
        "str_hex_bare_int",
        msg="'0x1' (bare hex integer) converts to 1.0",
        value="0x1",
        expected=1.0,
    ),
    ToDoubleTest(
        "str_hex_bare_ff",
        msg="'0xff' (bare hex integer) converts to 255.0",
        value="0xff",
        expected=255.0,
    ),
    # String: hex float errors.
    ToDoubleTest(
        "str_hex_err_no_digits",
        msg="'0x' (prefix only) is a conversion failure",
        value="0x",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_hex_err_p_no_exp",
        msg="'0x1p' (missing exponent digits) is a conversion failure",
        value="0x1p",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_hex_err_no_sig",
        msg="'0xp0' (missing significand digits) is a conversion failure",
        value="0xp0",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_hex_err_dot_only",
        msg="'0x.p0' (dot but no digits) is a conversion failure",
        value="0x.p0",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # String: general errors.
    ToDoubleTest(
        "str_alpha",
        msg="Alphabetic string is a conversion failure",
        value="abc",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_empty",
        msg="Empty string is a conversion failure",
        value="",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_leading_space",
        msg="Leading whitespace is a conversion failure",
        value=" 1",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_trailing_space",
        msg="Trailing whitespace is a conversion failure",
        value="1 ",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_embedded_space",
        msg="Embedded whitespace is a conversion failure",
        value="1 2",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_overflow",
        msg="Overflow string (> double max) is a conversion failure",
        value="1e309",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_underflow",
        msg="Underflow string (< double min subnormal) is a conversion failure",
        value="1e-400",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "str_partial_sci",
        msg="Incomplete scientific notation is a conversion failure",
        value="1.5e",
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # Datetime: converts to milliseconds since Unix epoch as double.
    ToDoubleTest(
        "datetime_epoch",
        msg="Epoch datetime converts to 0.0 ms",
        value=DATE_EPOCH,
        expected=0.0,
    ),
    ToDoubleTest(
        "datetime_one_day",
        msg="One day after epoch converts to 86400000.0 ms",
        value=datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        expected=86400000.0,
    ),
    ToDoubleTest(
        "datetime_before_epoch",
        msg="1 ms before epoch converts to -1.0",
        value=DATE_BEFORE_EPOCH,
        expected=-1.0,
    ),
    ToDoubleTest(
        "datetime_2024",
        msg="A modern date converts to its ms-since-epoch value",
        value=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        expected=1704067200000.0,
    ),
    # Binary: 4-byte float32 (little-endian IEEE 754).
    ToDoubleTest(
        "binary_f32_zero",
        msg="4-byte float32 zero binary converts to 0.0",
        value=_f32_zero,
        expected=0.0,
    ),
    ToDoubleTest(
        "binary_f32_one",
        msg="4-byte float32 1.0 binary converts to 1.0",
        value=_f32_one,
        expected=1.0,
    ),
    ToDoubleTest(
        "binary_f32_neg_one",
        msg="4-byte float32 -1.0 binary converts to -1.0",
        value=_f32_neg_one,
        expected=-1.0,
    ),
    ToDoubleTest(
        "binary_f32_two",
        msg="4-byte float32 2.0 binary converts to 2.0",
        value=_f32_two,
        expected=2.0,
    ),
    # Binary: 8-byte float64 (little-endian IEEE 754).
    ToDoubleTest(
        "binary_f64_zero",
        msg="8-byte float64 zero binary converts to 0.0",
        value=_f64_zero,
        expected=0.0,
    ),
    ToDoubleTest(
        "binary_f64_one",
        msg="8-byte float64 1.0 binary converts to 1.0",
        value=_f64_one,
        expected=1.0,
    ),
    ToDoubleTest(
        "binary_f64_neg_one",
        msg="8-byte float64 -1.0 binary converts to -1.0",
        value=_f64_neg_one,
        expected=-1.0,
    ),
    ToDoubleTest(
        "binary_f64_1_5",
        msg="8-byte float64 1.5 binary converts to 1.5",
        value=_f64_1_5,
        expected=1.5,
    ),
    # Binary: wrong lengths are conversion failures.
    ToDoubleTest(
        "binary_empty",
        msg="0-byte binary is a conversion failure",
        value=Binary(b""),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "binary_one_byte",
        msg="1-byte binary is a conversion failure",
        value=Binary(b"\x00"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "binary_three_bytes",
        msg="3-byte binary is a conversion failure",
        value=Binary(b"\x00\x00\x00"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "binary_five_bytes",
        msg="5-byte binary is a conversion failure",
        value=Binary(b"\x00\x00\x00\x00\x00"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # Unsupported BSON types are conversion failures.
    ToDoubleTest(
        "type_object",
        msg="Object BSON type is a conversion failure",
        value={"$literal": {"a": 1}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "type_objectid",
        msg="ObjectId BSON type is a conversion failure",
        value=ObjectId("000000000000000000000000"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "type_regex",
        msg="Regex BSON type is a conversion failure",
        value=Regex("abc"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "type_timestamp",
        msg="Timestamp BSON type is a conversion failure",
        value=Timestamp(0, 1),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "type_code",
        msg="Code BSON type is a conversion failure",
        value=Code("function(){}"),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "type_minkey",
        msg="MinKey BSON type is a conversion failure",
        value=MinKey(),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "type_maxkey",
        msg="MaxKey BSON type is a conversion failure",
        value=MaxKey(),
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ToDoubleTest(
        "type_array",
        msg="Array value (from $literal) is a conversion failure",
        value={"$literal": [1, 2]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# NaN tests are kept separate because NaN != NaN under IEEE 754,
# so they require assertSuccessNaN rather than assert_expression_result.
TODOUBLE_NAN_TESTS: list[ToDoubleTest] = [
    ToDoubleTest("double_nan", msg="double NaN passes through as NaN", value=FLOAT_NAN),
    ToDoubleTest("dec128_nan", msg="Decimal128 nan converts to double NaN", value=DECIMAL128_NAN),
    ToDoubleTest("str_nan", msg="'NaN' string converts to double NaN", value="NaN"),
    ToDoubleTest("str_nan_lower", msg="'nan' string converts to double NaN", value="nan"),
]


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_BASIC_TESTS))
@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_basic(collection, expr_fn, test):
    """$toDouble converts supported BSON types and rejects unsupported ones."""
    result = execute_expression(collection, expr_fn(test))
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_NAN_TESTS))
@pytest.mark.parametrize("expr_fn", _EXPR_FORMS)
def test_toDouble_nan(collection, expr_fn, test):
    """$toDouble should produce NaN for NaN-valued inputs."""
    result = execute_expression(collection, expr_fn(test))
    assertSuccessNaN(result, [{"result": FLOAT_NAN}], msg=test.msg)
