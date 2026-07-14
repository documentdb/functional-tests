"""$toDouble datetime and binary conversion tests, and unsupported BSON type errors."""

import struct
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

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
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DOUBLE_ONE_AND_HALF,
    DOUBLE_ZERO,
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

# Property [Datetime]: $toDouble converts datetime to milliseconds since Unix epoch as double.
TODOUBLE_DATETIME_TESTS: list[ExpressionTestCase] = [
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
]

# Property [Binary]: $toDouble interprets 4-byte binary as IEEE 754 float32 and 8-byte binary
# as IEEE 754 float64; other lengths are conversion failures.
TODOUBLE_BINARY_VALID_TESTS: list[ExpressionTestCase] = [
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
]

TODOUBLE_BINARY_ERROR_TESTS: list[ExpressionTestCase] = [
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
]

# Property [Unsupported Types]: $toDouble fails with a conversion error for BSON types it
# cannot convert (object, ObjectId, regex, timestamp, code, MinKey, MaxKey, array).
TODOUBLE_UNSUPPORTED_TYPE_TESTS: list[ExpressionTestCase] = [
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

TODOUBLE_DATETIME_BINARY_TESTS = (
    TODOUBLE_DATETIME_TESTS
    + TODOUBLE_BINARY_VALID_TESTS
    + TODOUBLE_BINARY_ERROR_TESTS
    + TODOUBLE_UNSUPPORTED_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TODOUBLE_DATETIME_BINARY_TESTS))
def test_toDouble_datetime_binary(collection, test: ExpressionTestCase):
    """$toDouble converts datetime and binary inputs; rejects unsupported BSON types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
