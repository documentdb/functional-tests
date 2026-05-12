from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Format Ignored]: format is silently ignored for conversions that do
# not involve string-to-binData or binData-to-string.
CONVERT_FORMAT_IGNORED_TESTS: list[ConvertTest] = [
    ConvertTest(
        "format_ignored_string_to_int",
        input="42",
        to="int",
        format="hex",
        expected=42,
        msg="$convert should ignore format for string to int",
    ),
    ConvertTest(
        "format_ignored_int_to_long",
        input=42,
        to="long",
        format="base64",
        expected=Int64(42),
        msg="$convert should ignore format for int to long",
    ),
    ConvertTest(
        "format_ignored_int_to_double",
        input=42,
        to="double",
        format="utf8",
        expected=42.0,
        msg="$convert should ignore format for int to double",
    ),
    ConvertTest(
        "format_ignored_int_to_decimal",
        input=42,
        to="decimal",
        format="base64",
        expected=Decimal128("42"),
        msg="$convert should ignore format for int to decimal",
    ),
    ConvertTest(
        "format_ignored_int_to_string",
        input=42,
        to="string",
        format="base64",
        expected="42",
        msg="$convert should ignore format for int to string",
    ),
    ConvertTest(
        "format_ignored_int_to_bool",
        input=42,
        to="bool",
        format="base64",
        expected=True,
        msg="$convert should ignore format for int to bool",
    ),
    ConvertTest(
        "format_ignored_string_to_date",
        input="2024-06-15T12:30:45Z",
        to="date",
        format="base64",
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
        msg="$convert should ignore format for string to date",
    ),
    ConvertTest(
        "format_ignored_string_to_objectId",
        input="507f1f77bcf86cd799439011",
        to="objectId",
        format="base64",
        expected=ObjectId("507f1f77bcf86cd799439011"),
        msg="$convert should ignore format for string to objectId",
    ),
    ConvertTest(
        "format_ignored_null_for_non_bindata",
        input=42,
        to="string",
        format=None,
        expected="42",
        msg="$convert should ignore null format for non-binData conversion",
    ),
]

# Property [Format Encoding Details]: each format has specific encoding rules
# for character sets, padding, case sensitivity, and byte handling.
CONVERT_FORMAT_ENCODING_TESTS: list[ConvertTest] = [
    ConvertTest(
        "format_base64url_with_padding",
        input="aGVsbG8=",
        to="binData",
        format="base64url",
        expected=b"hello",
        msg="$convert should accept base64url input with padding",
    ),
    ConvertTest(
        "format_base64_plus_slash",
        input="a+b/cA==",
        to="binData",
        format="base64",
        expected=b"k\xe6\xffp",
        msg="$convert should accept +/ characters in base64 input",
    ),
    ConvertTest(
        "format_base64url_dash_underscore",
        input="a-b_cA",
        to="binData",
        format="base64url",
        expected=b"k\xe6\xffp",
        msg="$convert should accept -_ characters in base64url input",
    ),
    ConvertTest(
        "format_hex_lowercase_input",
        input="68656c6c6f",
        to="binData",
        format="hex",
        expected=b"hello",
        msg="$convert should accept lowercase hex input",
    ),
    ConvertTest(
        "format_hex_mixed_case_input",
        input="68656C6c6F",
        to="binData",
        format="hex",
        expected=b"hello",
        msg="$convert should accept mixed-case hex input",
    ),
    ConvertTest(
        "format_utf8_null_bytes",
        input=Binary(b"hel\x00lo"),
        to="string",
        format="utf8",
        expected="hel\x00lo",
        msg="$convert should preserve null bytes in utf8 format",
    ),
    ConvertTest(
        "format_utf8_multibyte",
        input=Binary("café".encode()),
        to="string",
        format="utf8",
        expected="café",
        msg="$convert should preserve multi-byte UTF-8 characters in binData to string",
    ),
    ConvertTest(
        "format_utf8_multibyte_to_bindata",
        input="café",
        to="binData",
        format="utf8",
        expected="café".encode(),
        msg="$convert should preserve multi-byte UTF-8 characters in string to binData",
    ),
    ConvertTest(
        "format_base64_empty",
        input="",
        to="binData",
        format="base64",
        expected=b"",
        msg="$convert should accept empty base64 string",
    ),
    ConvertTest(
        "format_base64url_empty",
        input="",
        to="binData",
        format="base64url",
        expected=b"",
        msg="$convert should accept empty base64url string",
    ),
    ConvertTest(
        "format_hex_empty",
        input="",
        to="binData",
        format="hex",
        expected=b"",
        msg="$convert should accept empty hex string",
    ),
    ConvertTest(
        "format_utf8_empty",
        input=Binary(b""),
        to="string",
        format="utf8",
        expected="",
        msg="$convert should accept empty binData for utf8 format",
    ),
]

# Property [Format UUID Flexibility]: uuid format accepts any valid UUID string
# regardless of version, and subtype 4 binData can use non-uuid formats for
# binData-to-string conversion.
CONVERT_FORMAT_UUID_FLEXIBILITY_TESTS: list[ConvertTest] = [
    ConvertTest(
        "format_uuid_accepts_v1",
        input="6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(
            b"\x6b\xa7\xb8\x10\x9d\xad\x11\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8",
            4,
        ),
        msg="$convert should accept UUIDv1 string with uuid format",
    ),
    ConvertTest(
        "format_uuid_accepts_v2",
        input="6ba7b811-9dad-21d1-80b4-00c04fd430c8",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(
            b"\x6b\xa7\xb8\x11\x9d\xad\x21\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8",
            4,
        ),
        msg="$convert should accept UUIDv2 string with uuid format",
    ),
    ConvertTest(
        "format_uuid_accepts_v3",
        input="6ba7b811-9dad-31d1-80b4-00c04fd430c8",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(
            b"\x6b\xa7\xb8\x11\x9d\xad\x31\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8",
            4,
        ),
        msg="$convert should accept UUIDv3 string with uuid format",
    ),
    ConvertTest(
        "format_uuid_accepts_v5",
        input="6ba7b812-9dad-51d1-80b4-00c04fd430c8",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(
            b"\x6b\xa7\xb8\x12\x9d\xad\x51\xd1\x80\xb4\x00\xc0\x4f\xd4\x30\xc8",
            4,
        ),
        msg="$convert should accept UUIDv5 string with uuid format",
    ),
    ConvertTest(
        "format_uuid_accepts_v6",
        input="1ef21d2f-1207-6000-8000-000000000001",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(
            b"\x1e\xf2\x1d\x2f\x12\x07\x60\x00\x80\x00\x00\x00\x00\x00\x00\x01",
            4,
        ),
        msg="$convert should accept UUIDv6 string with uuid format",
    ),
    ConvertTest(
        "format_uuid_accepts_v7",
        input="018f6b2e-7b3a-7def-8000-000000000001",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(
            b"\x01\x8f\x6b\x2e\x7b\x3a\x7d\xef\x80\x00\x00\x00\x00\x00\x00\x01",
            4,
        ),
        msg="$convert should accept UUIDv7 string with uuid format",
    ),
    ConvertTest(
        "format_uuid_accepts_v8",
        input="018f6b2e-7b3a-8def-8000-000000000001",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(
            b"\x01\x8f\x6b\x2e\x7b\x3a\x8d\xef\x80\x00\x00\x00\x00\x00\x00\x01",
            4,
        ),
        msg="$convert should accept UUIDv8 string with uuid format",
    ),
    ConvertTest(
        "format_uuid_accepts_nil",
        input="00000000-0000-0000-0000-000000000000",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(b"\x00" * 16, 4),
        msg="$convert should accept nil UUID string with uuid format",
    ),
    ConvertTest(
        "format_uuid_accepts_max",
        input="ffffffff-ffff-ffff-ffff-ffffffffffff",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(b"\xff" * 16, 4),
        msg="$convert should accept max UUID string with uuid format",
    ),
    ConvertTest(
        "format_sub4_base64",
        input=Binary(
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
            4,
        ),
        to="string",
        format="base64",
        expected="AQIDBAUGBwgJCgsMDQ4PEA==",
        msg="$convert should allow base64 format for subtype 4 binData to string",
    ),
    ConvertTest(
        "format_sub4_hex",
        input=Binary(
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
            4,
        ),
        to="string",
        format="hex",
        expected="0102030405060708090A0B0C0D0E0F10",
        msg="$convert should allow hex format for subtype 4 binData to string",
    ),
]

CONVERT_FORMAT_SUCCESS_TESTS = (
    CONVERT_FORMAT_IGNORED_TESTS
    + CONVERT_FORMAT_ENCODING_TESTS
    + CONVERT_FORMAT_UUID_FLEXIBILITY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_FORMAT_SUCCESS_TESTS))
def test_convert_format(collection, test_case: ConvertTest):
    """Test $convert format behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
