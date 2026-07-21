"""$toLong datetime and binary conversion tests, and unsupported BSON type errors."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64

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
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Datetime]: $toLong converts datetime to milliseconds since Unix epoch as Int64.
TOLONG_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "datetime_epoch",
        msg="Epoch datetime converts to Int64(0)",
        expression={"$toLong": datetime(1970, 1, 1, tzinfo=timezone.utc)},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "datetime_1ms_after_epoch",
        msg="1ms after epoch converts to Int64(1)",
        expression={"$toLong": datetime(1970, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc)},
        expected=Int64(1),
    ),
    ExpressionTestCase(
        "datetime_1ms_before_epoch",
        msg="1ms before epoch converts to Int64(-1)",
        expression={"$toLong": datetime(1969, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expected=Int64(-1),
    ),
    ExpressionTestCase(
        "datetime_pre_epoch",
        msg="Pre-epoch datetime produces negative milliseconds",
        expression={"$toLong": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expected=Int64(-1000),
    ),
    ExpressionTestCase(
        "datetime_with_ms",
        msg="Modern datetime preserves millisecond precision",
        expression={"$toLong": datetime(2024, 6, 15, 12, 30, 45, 123000, tzinfo=timezone.utc)},
        expected=Int64(1_718_454_645_123),
    ),
    ExpressionTestCase(
        "datetime_far_future",
        msg="Far-future datetime converts correctly",
        expression={"$toLong": datetime(9999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc)},
        expected=Int64(253_402_300_799_999),
    ),
    ExpressionTestCase(
        "datetime_far_past",
        msg="Far-past datetime converts correctly",
        expression={"$toLong": datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expected=Int64(-62_135_596_800_000),
    ),
]

# Property [Binary Conversion]: Binary values of exactly 1, 2, 4, or 8 bytes are
# interpreted as signed little-endian integers.
TOLONG_BINARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_1byte_zero",
        msg="1-byte Binary 0x00 converts to Int64(0)",
        expression={"$toLong": Binary(b"\x00")},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "binary_1byte_max",
        msg="1-byte Binary 0x7F converts to Int64(127)",
        expression={"$toLong": Binary(b"\x7f")},
        expected=Int64(127),
    ),
    ExpressionTestCase(
        "binary_1byte_min",
        msg="1-byte Binary 0x80 converts to Int64(-128)",
        expression={"$toLong": Binary(b"\x80")},
        expected=Int64(-128),
    ),
    ExpressionTestCase(
        "binary_1byte_neg_one",
        msg="1-byte Binary 0xFF converts to Int64(-1)",
        expression={"$toLong": Binary(b"\xff")},
        expected=Int64(-1),
    ),
    ExpressionTestCase(
        "binary_2byte_max",
        msg="2-byte Binary converts to int16 max (Int64(32767))",
        expression={"$toLong": Binary(b"\xff\x7f")},
        expected=Int64(32767),
    ),
    ExpressionTestCase(
        "binary_2byte_min",
        msg="2-byte Binary converts to int16 min (Int64(-32768))",
        expression={"$toLong": Binary(b"\x00\x80")},
        expected=Int64(-32768),
    ),
    ExpressionTestCase(
        "binary_4byte_max",
        msg="4-byte Binary converts to int32 max",
        expression={"$toLong": Binary(b"\xff\xff\xff\x7f")},
        expected=Int64(INT32_MAX),
    ),
    ExpressionTestCase(
        "binary_4byte_min",
        msg="4-byte Binary converts to int32 min",
        expression={"$toLong": Binary(b"\x00\x00\x00\x80")},
        expected=Int64(INT32_MIN),
    ),
    ExpressionTestCase(
        "binary_8byte_max",
        msg="8-byte Binary converts to int64 max",
        expression={"$toLong": Binary(b"\xff\xff\xff\xff\xff\xff\xff\x7f")},
        expected=INT64_MAX,
    ),
    ExpressionTestCase(
        "binary_8byte_min",
        msg="8-byte Binary converts to int64 min",
        expression={"$toLong": Binary(b"\x00\x00\x00\x00\x00\x00\x00\x80")},
        expected=INT64_MIN,
    ),
    ExpressionTestCase(
        "binary_8byte_zero",
        msg="8-byte all-zeros Binary converts to Int64(0)",
        expression={"$toLong": Binary(b"\x00\x00\x00\x00\x00\x00\x00\x00")},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "binary_subtype_2_empty_payload",
        msg="Subtype 2 empty payload (4-byte header only) converts to Int64(0)",
        expression={"$toLong": Binary(b"", 2)},
        expected=INT64_ZERO,
    ),
    ExpressionTestCase(
        "binary_subtype_3",
        msg="Binary subtype 3 converts by payload length (1 byte)",
        expression={"$toLong": Binary(b"\x7f", 3)},
        expected=Int64(127),
    ),
]

# Property [Binary Conversion Errors]: Binary values of sizes other than 1, 2, 4, or 8 bytes
# produce a conversion error.
TOLONG_BINARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_err_0byte",
        msg="0-byte Binary is a conversion failure",
        expression={"$toLong": Binary(b"", 0)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_err_3byte",
        msg="3-byte Binary is a conversion failure",
        expression={"$toLong": Binary(b"\x01\x02\x03")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_err_5byte",
        msg="5-byte Binary is a conversion failure",
        expression={"$toLong": Binary(b"\x01" * 5)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_err_9byte",
        msg="9-byte Binary is a conversion failure",
        expression={"$toLong": Binary(b"\x01" * 9)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_err_uuid_subtype",
        msg="UUID subtype Binary (16 bytes) is a conversion failure",
        expression={"$toLong": Binary(b"\x01" * 16, 4)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_err_subtype_2",
        msg="Binary subtype 2 (old binary) with 1-byte payload is a conversion failure (5-byte wire length)",  # noqa: E501
        expression={"$toLong": Binary(b"\x7f", 2)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [Unsupported Types — literal-wrapped]: OBJECT and ARRAY must be wrapped in
# $literal to prevent MongoDB from interpreting them as expression syntax. The remaining
# unsupported BSON types (ObjectId, Regex, Timestamp, Code, MinKey, MaxKey) are covered
# by generate_bson_rejection_test_cases() in test_toLong_return_type.py.
#
# The nested-array case wraps its value in $literal so the outer single-element array
# can be unwrapped by the arity rule, leaving the inner array as the actual argument.
TOLONG_UNSUPPORTED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "type_object",
        msg="Object BSON type is a conversion failure",
        expression={"$toLong": {"$literal": {"key": "val"}}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_array",
        msg="Array value (from $literal) is a conversion failure",
        expression={"$toLong": {"$literal": [1, 2]}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_nested_array",
        msg="Outer single-element array unwraps at parse time; inner array arg is a conversion failure",  # noqa: E501
        expression={"$toLong": [["42"]]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOLONG_DATETIME_BINARY_TESTS = (
    TOLONG_DATETIME_TESTS
    + TOLONG_BINARY_TESTS
    + TOLONG_BINARY_ERROR_TESTS
    + TOLONG_UNSUPPORTED_TYPE_TESTS
)


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOLONG_DATETIME_BINARY_TESTS, "$toLong", "long")),
)
def test_toLong_datetime_binary(collection, test: ExpressionTestCase):
    """$toLong converts datetime and binary inputs; rejects unsupported BSON types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
