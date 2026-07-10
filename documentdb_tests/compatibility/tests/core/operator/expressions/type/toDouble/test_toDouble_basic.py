"""$toDouble basic tests: null/missing, boolean, integer, double identity,
decimal128, string, hex float, datetime, binary, and unsupported type errors."""

import struct
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
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
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_HALF,
    DOUBLE_MAX,
    DOUBLE_MAX_SAFE_INTEGER,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ONE_AND_HALF,
    DOUBLE_PRECISION_LOSS,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_ZERO,
    MISSING,
)

# Pre-computed binary values: 4-byte little-endian float32.
_f32_zero = Binary(struct.pack("<f", DOUBLE_ZERO))
_f32_one = Binary(struct.pack("<f", 1.0))
_f32_neg_one = Binary(struct.pack("<f", -1.0))
_f32_two = Binary(struct.pack("<f", 2.0))

# Pre-computed binary values: 8-byte little-endian float64.
_f64_zero = Binary(struct.pack("<d", DOUBLE_ZERO))
_f64_one = Binary(struct.pack("<d", 1.0))
_f64_neg_one = Binary(struct.pack("<d", -1.0))
_f64_1_5 = Binary(struct.pack("<d", DOUBLE_ONE_AND_HALF))


TODOUBLE_BASIC_TESTS: list[ExpressionTestCase] = [
    # Null / missing.
    ExpressionTestCase(
        "null", msg="Should return null for null", expression={"$toDouble": None}, expected=None
    ),
    ExpressionTestCase(
        "missing",
        msg="Should return null for missing",
        expression={"$toDouble": MISSING},
        expected=None,
    ),
    # Boolean.
    ExpressionTestCase(
        "bool_true", msg="True converts to 1.0", expression={"$toDouble": True}, expected=1.0
    ),
    ExpressionTestCase(
        "bool_false",
        msg="False converts to positive 0.0",
        expression={"$toDouble": False},
        expected=DOUBLE_ZERO,
    ),
    # int32.
    ExpressionTestCase(
        "int32_zero",
        msg="int32 zero converts to 0.0",
        expression={"$toDouble": 0},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "int32_one",
        msg="int32 1 converts exactly to 1.0",
        expression={"$toDouble": 1},
        expected=1.0,
    ),
    ExpressionTestCase(
        "int32_neg_one",
        msg="int32 -1 converts exactly to -1.0",
        expression={"$toDouble": -1},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "int32_max",
        msg="int32 max converts exactly",
        expression={"$toDouble": INT32_MAX},
        expected=2147483647.0,
    ),
    ExpressionTestCase(
        "int32_min",
        msg="int32 min converts exactly",
        expression={"$toDouble": INT32_MIN},
        expected=-2147483648.0,
    ),
    # int64.
    ExpressionTestCase(
        "int64_zero",
        msg="int64 zero converts to 0.0",
        expression={"$toDouble": INT64_ZERO},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "int64_one", msg="int64 1 converts to 1.0", expression={"$toDouble": Int64(1)}, expected=1.0
    ),
    ExpressionTestCase(
        "int64_safe_max",
        msg="int64 at 2^53 (max safe integer) converts exactly",
        expression={"$toDouble": Int64(DOUBLE_MAX_SAFE_INTEGER)},
        expected=9007199254740992.0,
    ),
    ExpressionTestCase(
        "int64_above_safe",
        msg="int64 above 2^53 loses the last bit of precision",
        expression={"$toDouble": Int64(DOUBLE_PRECISION_LOSS)},
        expected=9007199254740992.0,
    ),
    ExpressionTestCase(
        "int64_neg_one",
        msg="int64 -1 converts to -1.0",
        expression={"$toDouble": Int64(-1)},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "int64_max",
        msg="int64 max converts with precision loss",
        expression={"$toDouble": INT64_MAX},
        expected=DOUBLE_FROM_INT64_MAX,
    ),
    ExpressionTestCase(
        "int64_max_minus_one",
        msg="int64 max-1 rounds to the same double as int64 max",
        expression={"$toDouble": INT64_MAX_MINUS_1},
        expected=DOUBLE_FROM_INT64_MAX,
    ),
    ExpressionTestCase(
        "int64_min",
        msg="int64 min converts to -2^63 representation",
        expression={"$toDouble": INT64_MIN},
        expected=-DOUBLE_FROM_INT64_MAX,
    ),
    # Double identity (passthrough).
    ExpressionTestCase(
        "double_zero",
        msg="0.0 passes through unchanged",
        expression={"$toDouble": DOUBLE_ZERO},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "double_neg_zero",
        msg="-0.0 passes through preserving sign",
        expression={"$toDouble": DOUBLE_NEGATIVE_ZERO},
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "double_inf",
        msg="+Inf passes through unchanged",
        expression={"$toDouble": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "double_neg_inf",
        msg="-Inf passes through unchanged",
        expression={"$toDouble": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "double_one",
        msg="1.0 passes through unchanged",
        expression={"$toDouble": 1.0},
        expected=1.0,
    ),
    ExpressionTestCase(
        "double_pi",
        msg="pi passes through unchanged",
        expression={"$toDouble": 3.141592653589793},
        expected=3.141592653589793,
    ),
    ExpressionTestCase(
        "double_large",
        msg="Large double passes through unchanged",
        expression={"$toDouble": DOUBLE_MAX},
        expected=DOUBLE_MAX,
    ),
    ExpressionTestCase(
        "double_subnormal",
        msg="Minimum positive subnormal double passes through unchanged",
        expression={"$toDouble": DOUBLE_MIN_SUBNORMAL},
        expected=DOUBLE_MIN_SUBNORMAL,
    ),
    ExpressionTestCase(
        "double_neg_subnormal",
        msg="Minimum negative subnormal double passes through unchanged",
        expression={"$toDouble": DOUBLE_MIN_NEGATIVE_SUBNORMAL},
        expected=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    ),
    # Decimal128.
    ExpressionTestCase(
        "dec128_zero",
        msg="Decimal128 zero converts to 0.0",
        expression={"$toDouble": DECIMAL128_ZERO},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "dec128_neg_zero",
        msg="Decimal128 -0 converts to -0.0 preserving sign",
        expression={"$toDouble": DECIMAL128_NEGATIVE_ZERO},
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "dec128_inf",
        msg="Decimal128 Infinity converts to +Inf",
        expression={"$toDouble": DECIMAL128_INFINITY},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "dec128_neg_inf",
        msg="Decimal128 -Infinity converts to -Inf",
        expression={"$toDouble": DECIMAL128_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "dec128_one",
        msg="Decimal128 1 converts to 1.0",
        expression={"$toDouble": Decimal128("1")},
        expected=1.0,
    ),
    ExpressionTestCase(
        "dec128_trailing_zero",
        msg="Decimal128 trailing zero normalizes correctly",
        expression={"$toDouble": DECIMAL128_TRAILING_ZERO},
        expected=1.0,
    ),
    ExpressionTestCase(
        "dec128_many_trailing_zeros",
        msg="Decimal128 with many trailing zeros normalizes correctly",
        expression={"$toDouble": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=1.0,
    ),
    ExpressionTestCase(
        "dec128_neg",
        msg="Decimal128 negative value converts correctly",
        expression={"$toDouble": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=DOUBLE_NEGATIVE_ONE_AND_HALF,
    ),
    ExpressionTestCase(
        "dec128_overflow",
        msg="Decimal128 value exceeding double max is a conversion failure",
        expression={"$toDouble": DECIMAL128_MAX},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "dec128_neg_overflow",
        msg="Decimal128 most-negative value exceeding double range is a conversion failure",
        expression={"$toDouble": DECIMAL128_MIN},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "dec128_underflow",
        msg="Decimal128 too small for double underflows to 0.0",
        expression={"$toDouble": DECIMAL128_MIN_POSITIVE},
        expected=DOUBLE_ZERO,
    ),
    # String: valid numeric conversions.
    ExpressionTestCase(
        "str_zero", msg="'0' converts to 0.0", expression={"$toDouble": "0"}, expected=DOUBLE_ZERO
    ),
    ExpressionTestCase(
        "str_one", msg="'1' converts to 1.0", expression={"$toDouble": "1"}, expected=1.0
    ),
    ExpressionTestCase(
        "str_neg_one", msg="'-1' converts to -1.0", expression={"$toDouble": "-1"}, expected=-1.0
    ),
    ExpressionTestCase(
        "str_plus_one", msg="'+1' converts to 1.0", expression={"$toDouble": "+1"}, expected=1.0
    ),
    ExpressionTestCase(
        "str_decimal",
        msg="'1.5' converts to 1.5",
        expression={"$toDouble": "1.5"},
        expected=DOUBLE_ONE_AND_HALF,
    ),
    ExpressionTestCase(
        "str_dot_five",
        msg="'.5' converts to 0.5",
        expression={"$toDouble": ".5"},
        expected=DOUBLE_HALF,
    ),
    ExpressionTestCase(
        "str_neg_zero",
        msg="'-0' converts to -0.0",
        expression={"$toDouble": "-0"},
        expected=DOUBLE_NEGATIVE_ZERO,
    ),
    ExpressionTestCase(
        "str_sci_pos",
        msg="'1e10' (scientific) converts correctly",
        expression={"$toDouble": "1e10"},
        expected=1e10,
    ),
    ExpressionTestCase(
        "str_sci_neg_exp",
        msg="'1.5e-3' (scientific negative exponent) converts correctly",
        expression={"$toDouble": "1.5e-3"},
        expected=1.5e-3,
    ),
    ExpressionTestCase(
        "str_sci_upper",
        msg="'1E10' (uppercase E) converts correctly",
        expression={"$toDouble": "1E10"},
        expected=1e10,
    ),
    ExpressionTestCase(
        "str_inf",
        msg="'Infinity' converts to +Inf",
        expression={"$toDouble": "Infinity"},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "str_neg_inf",
        msg="'-Infinity' converts to -Inf",
        expression={"$toDouble": "-Infinity"},
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    ExpressionTestCase(
        "str_plus_inf",
        msg="'+Infinity' converts to +Inf",
        expression={"$toDouble": "+Infinity"},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "str_inf_short",
        msg="'inf' converts to +Inf",
        expression={"$toDouble": "inf"},
        expected=FLOAT_INFINITY,
    ),
    ExpressionTestCase(
        "str_neg_inf_short",
        msg="'-inf' converts to -Inf",
        expression={"$toDouble": "-inf"},
        expected=FLOAT_NEGATIVE_INFINITY,
    ),
    # String: hex float.
    ExpressionTestCase(
        "str_hex_zero",
        msg="'0x0p0' converts to 0.0",
        expression={"$toDouble": "0x0p0"},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "str_hex_one",
        msg="'0x1p0' converts to 1.0",
        expression={"$toDouble": "0x1p0"},
        expected=1.0,
    ),
    ExpressionTestCase(
        "str_hex_two",
        msg="'0x1p1' converts to 2.0",
        expression={"$toDouble": "0x1p1"},
        expected=2.0,
    ),
    ExpressionTestCase(
        "str_hex_half",
        msg="'0x1p-1' converts to 0.5",
        expression={"$toDouble": "0x1p-1"},
        expected=DOUBLE_HALF,
    ),
    ExpressionTestCase(
        "str_hex_frac",
        msg="'0x1.8p1' converts to 3.0",
        expression={"$toDouble": "0x1.8p1"},
        expected=3.0,
    ),
    ExpressionTestCase(
        "str_hex_neg",
        msg="'-0x1p0' converts to -1.0",
        expression={"$toDouble": "-0x1p0"},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "str_hex_plus",
        msg="'+0x1p0' converts to 1.0",
        expression={"$toDouble": "+0x1p0"},
        expected=1.0,
    ),
    ExpressionTestCase(
        "str_hex_upper",
        msg="'0X1P0' (uppercase) converts to 1.0",
        expression={"$toDouble": "0X1P0"},
        expected=1.0,
    ),
    ExpressionTestCase(
        "str_hex_ff",
        msg="'0xffp0' converts to 255.0",
        expression={"$toDouble": "0xffp0"},
        expected=255.0,
    ),
    ExpressionTestCase(
        "str_hex_bare_int",
        msg="'0x1' (bare hex integer) converts to 1.0",
        expression={"$toDouble": "0x1"},
        expected=1.0,
    ),
    ExpressionTestCase(
        "str_hex_bare_ff",
        msg="'0xff' (bare hex integer) converts to 255.0",
        expression={"$toDouble": "0xff"},
        expected=255.0,
    ),
    # String: hex float errors.
    ExpressionTestCase(
        "str_hex_err_no_digits",
        msg="'0x' (prefix only) is a conversion failure",
        expression={"$toDouble": "0x"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_hex_err_p_no_exp",
        msg="'0x1p' (missing exponent digits) is a conversion failure",
        expression={"$toDouble": "0x1p"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_hex_err_no_sig",
        msg="'0xp0' (missing significand digits) is a conversion failure",
        expression={"$toDouble": "0xp0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_hex_err_dot_only",
        msg="'0x.p0' (dot but no digits) is a conversion failure",
        expression={"$toDouble": "0x.p0"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # String: general errors.
    ExpressionTestCase(
        "str_alpha",
        msg="Alphabetic string is a conversion failure",
        expression={"$toDouble": "abc"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_empty",
        msg="Empty string is a conversion failure",
        expression={"$toDouble": ""},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_leading_space",
        msg="Leading whitespace is a conversion failure",
        expression={"$toDouble": " 1"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_trailing_space",
        msg="Trailing whitespace is a conversion failure",
        expression={"$toDouble": "1 "},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_embedded_space",
        msg="Embedded whitespace is a conversion failure",
        expression={"$toDouble": "1 2"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_overflow",
        msg="Overflow string (> double max) is a conversion failure",
        expression={"$toDouble": "1e309"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_underflow",
        msg="Underflow string (< double min subnormal) is a conversion failure",
        expression={"$toDouble": "1e-400"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "str_partial_sci",
        msg="Incomplete scientific notation is a conversion failure",
        expression={"$toDouble": "1.5e"},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # Datetime: converts to milliseconds since Unix epoch as double.
    ExpressionTestCase(
        "datetime_epoch",
        msg="Epoch datetime converts to 0.0 ms",
        expression={"$toDouble": DATE_EPOCH},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "datetime_one_day",
        msg="One day after epoch converts to 86400000.0 ms",
        expression={"$toDouble": datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc)},
        expected=86400000.0,
    ),
    ExpressionTestCase(
        "datetime_before_epoch",
        msg="1 ms before epoch converts to -1.0",
        expression={"$toDouble": DATE_BEFORE_EPOCH},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "datetime_2024",
        msg="A modern date converts to its ms-since-epoch value",
        expression={"$toDouble": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expected=1704067200000.0,
    ),
    # Binary: 4-byte float32 (little-endian IEEE 754).
    ExpressionTestCase(
        "binary_f32_zero",
        msg="4-byte float32 zero binary converts to 0.0",
        expression={"$toDouble": _f32_zero},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "binary_f32_one",
        msg="4-byte float32 1.0 binary converts to 1.0",
        expression={"$toDouble": _f32_one},
        expected=1.0,
    ),
    ExpressionTestCase(
        "binary_f32_neg_one",
        msg="4-byte float32 -1.0 binary converts to -1.0",
        expression={"$toDouble": _f32_neg_one},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "binary_f32_two",
        msg="4-byte float32 2.0 binary converts to 2.0",
        expression={"$toDouble": _f32_two},
        expected=2.0,
    ),
    # Binary: 8-byte float64 (little-endian IEEE 754).
    ExpressionTestCase(
        "binary_f64_zero",
        msg="8-byte float64 zero binary converts to 0.0",
        expression={"$toDouble": _f64_zero},
        expected=DOUBLE_ZERO,
    ),
    ExpressionTestCase(
        "binary_f64_one",
        msg="8-byte float64 1.0 binary converts to 1.0",
        expression={"$toDouble": _f64_one},
        expected=1.0,
    ),
    ExpressionTestCase(
        "binary_f64_neg_one",
        msg="8-byte float64 -1.0 binary converts to -1.0",
        expression={"$toDouble": _f64_neg_one},
        expected=-1.0,
    ),
    ExpressionTestCase(
        "binary_f64_1_5",
        msg="8-byte float64 1.5 binary converts to 1.5",
        expression={"$toDouble": _f64_1_5},
        expected=DOUBLE_ONE_AND_HALF,
    ),
    # Binary: wrong lengths are conversion failures.
    ExpressionTestCase(
        "binary_empty",
        msg="0-byte binary is a conversion failure",
        expression={"$toDouble": Binary(b"")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_one_byte",
        msg="1-byte binary is a conversion failure",
        expression={"$toDouble": Binary(b"\x00")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_three_bytes",
        msg="3-byte binary is a conversion failure",
        expression={"$toDouble": Binary(b"\x00\x00\x00")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_five_bytes",
        msg="5-byte binary is a conversion failure",
        expression={"$toDouble": Binary(b"\x00\x00\x00\x00\x00")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    # Unsupported BSON types are conversion failures.
    ExpressionTestCase(
        "type_object",
        msg="Object BSON type is a conversion failure",
        expression={"$toDouble": {"$literal": {"a": 1}}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_objectid",
        msg="ObjectId BSON type is a conversion failure",
        expression={"$toDouble": ObjectId("000000000000000000000000")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_regex",
        msg="Regex BSON type is a conversion failure",
        expression={"$toDouble": Regex("abc")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_timestamp",
        msg="Timestamp BSON type is a conversion failure",
        expression={"$toDouble": Timestamp(0, 1)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_code",
        msg="Code BSON type is a conversion failure",
        expression={"$toDouble": Code("function(){}")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_minkey",
        msg="MinKey BSON type is a conversion failure",
        expression={"$toDouble": MinKey()},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_maxkey",
        msg="MaxKey BSON type is a conversion failure",
        expression={"$toDouble": MaxKey()},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_array",
        msg="Array value (from $literal) is a conversion failure",
        expression={"$toDouble": {"$literal": [1, 2]}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# NaN tests are kept separate because NaN != NaN under IEEE 754,
# so they require assertSuccessNaN rather than assert_expression_result.
TODOUBLE_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_nan", msg="double NaN passes through as NaN", expression={"$toDouble": FLOAT_NAN}
    ),
    ExpressionTestCase(
        "dec128_nan",
        msg="Decimal128 nan converts to double NaN",
        expression={"$toDouble": DECIMAL128_NAN},
    ),
    ExpressionTestCase(
        "str_nan", msg="'NaN' string converts to double NaN", expression={"$toDouble": "NaN"}
    ),
    ExpressionTestCase(
        "str_nan_lower", msg="'nan' string converts to double NaN", expression={"$toDouble": "nan"}
    ),
]


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_BASIC_TESTS))
def test_toDouble_basic(collection, test: ExpressionTestCase):
    """$toDouble converts supported BSON types and rejects unsupported ones."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_NAN_TESTS))
def test_toDouble_nan(collection, test: ExpressionTestCase):
    """$toDouble should produce NaN for NaN-valued inputs."""
    result = execute_expression(collection, test.expression)
    assertSuccessNaN(result, [{"result": FLOAT_NAN}], msg=test.msg)
