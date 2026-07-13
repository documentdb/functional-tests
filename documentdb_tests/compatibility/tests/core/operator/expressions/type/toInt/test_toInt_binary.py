"""$toInt binary conversion tests and unsupported BSON type errors."""

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
from documentdb_tests.framework.test_constants import INT32_MAX, INT32_MIN

# Property [Binary Conversion]: Binary values of exactly 1, 2, or 4 bytes are
# interpreted as signed little-endian integers, regardless of subtype (except subtype 2,
# which prepends a 4-byte length header on the wire).
_TOINT_BINARY_VALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_1byte_zero",
        msg="1-byte Binary 0x00 converts to 0",
        expression={"$toInt": Binary(b"\x00", 0)},
        expected=0,
    ),
    ExpressionTestCase(
        "binary_1byte_max",
        msg="1-byte Binary 0x7F converts to 127",
        expression={"$toInt": Binary(b"\x7f", 0)},
        expected=127,
    ),
    ExpressionTestCase(
        "binary_1byte_min",
        msg="1-byte Binary 0x80 converts to -128",
        expression={"$toInt": Binary(b"\x80", 0)},
        expected=-128,
    ),
    ExpressionTestCase(
        "binary_1byte_neg_one",
        msg="1-byte Binary 0xFF converts to -1",
        expression={"$toInt": Binary(b"\xff", 0)},
        expected=-1,
    ),
    ExpressionTestCase(
        "binary_2byte_int16_max",
        msg="2-byte Binary little-endian 0xFF7F converts to int16 max (32767)",
        expression={"$toInt": Binary(b"\xff\x7f", 0)},
        expected=32_767,
    ),
    ExpressionTestCase(
        "binary_2byte_int16_min",
        msg="2-byte Binary little-endian 0x0080 converts to int16 min (-32768)",
        expression={"$toInt": Binary(b"\x00\x80", 0)},
        expected=-32_768,
    ),
    ExpressionTestCase(
        "binary_4byte_int32_max",
        msg="4-byte Binary little-endian converts to int32 max",
        expression={"$toInt": Binary(b"\xff\xff\xff\x7f", 0)},
        expected=INT32_MAX,
    ),
    ExpressionTestCase(
        "binary_4byte_int32_min",
        msg="4-byte Binary little-endian converts to int32 min",
        expression={"$toInt": Binary(b"\x00\x00\x00\x80", 0)},
        expected=INT32_MIN,
    ),
    ExpressionTestCase(
        "binary_subtype_2_empty_payload",
        msg="Subtype 2 empty payload (4-byte length header only on wire) converts to 0",
        expression={"$toInt": Binary(b"", 2)},
        expected=0,
    ),
    ExpressionTestCase(
        "binary_subtype_3",
        msg="Subtype 3 (old UUID) 1-byte binary converts; subtype is ignored",
        expression={"$toInt": Binary(b"\x7f", 3)},
        expected=127,
    ),
    ExpressionTestCase(
        "binary_subtype_4",
        msg="Subtype 4 (UUID) 1-byte binary converts; subtype is ignored",
        expression={"$toInt": Binary(b"\x7f", 4)},
        expected=127,
    ),
    ExpressionTestCase(
        "binary_subtype_5",
        msg="Subtype 5 (MD5) 1-byte binary converts; subtype is ignored",
        expression={"$toInt": Binary(b"\x7f", 5)},
        expected=127,
    ),
    ExpressionTestCase(
        "binary_subtype_128",
        msg="Subtype 128 (user-defined) 1-byte binary converts; subtype is ignored",
        expression={"$toInt": Binary(b"\x7f", 128)},
        expected=127,
    ),
]

# Property [Binary Conversion Errors]: Binary values with lengths other than 1, 2, or 4
# bytes produce a conversion failure.
_TOINT_BINARY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_0byte",
        msg="0-byte binary is a conversion failure",
        expression={"$toInt": Binary(b"", 0)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_3byte",
        msg="3-byte binary is a conversion failure",
        expression={"$toInt": Binary(b"\x00" * 3, 0)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_5byte",
        msg="5-byte binary is a conversion failure",
        expression={"$toInt": Binary(b"\x00" * 5, 0)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_8byte",
        msg="8-byte binary is a conversion failure",
        expression={"$toInt": Binary(b"\x00" * 8, 0)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_16byte",
        msg="16-byte binary is a conversion failure",
        expression={"$toInt": Binary(b"\x00" * 16, 0)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_uuid_16byte",
        msg="UUID subtype 16-byte binary is a conversion failure",
        expression={"$toInt": Binary(b"\x00" * 16, 4)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "binary_subtype_2",
        msg="Subtype 2 (old binary) 1-byte payload becomes 5 bytes on wire; conversion failure",
        expression={"$toInt": Binary(b"\x7f", 2)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

# Property [Unsupported Types]: $toInt fails with a conversion error for BSON types it
# cannot convert (datetime, ObjectId, regex, timestamp, code, MinKey, MaxKey, object, array).
_TOINT_UNSUPPORTED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "type_object",
        msg="Object BSON type is a conversion failure",
        expression={"$toInt": {"$literal": {"key": "val"}}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_objectid",
        msg="ObjectId BSON type is a conversion failure",
        expression={"$toInt": ObjectId("000000000000000000000000")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_datetime",
        msg="Datetime BSON type is a conversion failure (unlike $toLong)",
        expression={"$toInt": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_timestamp",
        msg="Timestamp BSON type is a conversion failure",
        expression={"$toInt": Timestamp(1, 1)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_regex",
        msg="Regex BSON type is a conversion failure",
        expression={"$toInt": Regex("abc")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_code",
        msg="Code BSON type is a conversion failure",
        expression={"$toInt": Code("x")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_minkey",
        msg="MinKey BSON type is a conversion failure",
        expression={"$toInt": MinKey()},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_maxkey",
        msg="MaxKey BSON type is a conversion failure",
        expression={"$toInt": MaxKey()},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_array",
        msg="Nested array (unwrapped once; inner array hits type check) is a conversion failure",
        expression={"$toInt": {"$literal": [["42"]]}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TOINT_BINARY_TESTS = (
    _TOINT_BINARY_VALID_TESTS + _TOINT_BINARY_ERROR_TESTS + _TOINT_UNSUPPORTED_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TOINT_BINARY_TESTS))
def test_toInt_binary(collection, test: ExpressionTestCase):
    """$toInt converts 1/2/4-byte binary; rejects other lengths and unsupported BSON types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
