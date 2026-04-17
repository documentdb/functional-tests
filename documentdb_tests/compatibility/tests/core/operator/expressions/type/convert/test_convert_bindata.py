from __future__ import annotations

import struct

import pytest
from bson import Binary, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [String BinData Formats]: BinData-to-string conversion requires the
# format parameter and produces format-specific output.
CONVERT_STRING_BINDATA_FORMAT_TESTS: list[ConvertTest] = [
    ConvertTest(
        "string_bindata_base64",
        input=Binary(b">>>>"),
        to="string",
        format="base64",
        expected="Pj4+Pg==",
        msg="$convert should encode BinData as base64 with padding",
    ),
    ConvertTest(
        "string_bindata_base64url",
        input=Binary(b">>>>"),
        to="string",
        format="base64url",
        expected="Pj4-Pg",
        msg="$convert should encode BinData as base64url with URL-safe chars and no padding",
    ),
    ConvertTest(
        "string_bindata_utf8",
        input=Binary(b"hello"),
        to="string",
        format="utf8",
        expected="hello",
        msg="$convert should decode BinData as UTF-8 string",
    ),
    ConvertTest(
        "string_bindata_hex",
        input=Binary(b"hello"),
        to="string",
        format="hex",
        expected="68656C6C6F",
        msg="$convert should encode BinData as uppercase hex",
    ),
    ConvertTest(
        "string_bindata_uuid",
        input=Binary(
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
            4,
        ),
        to="string",
        format="uuid",
        expected="01020304-0506-0708-090a-0b0c0d0e0f10",
        msg="$convert should format subtype 4 BinData as UUID string",
    ),
]

# Property [BinData Core Conversions]: each supported numeric source type
# converts to binData with the correct byte representation.
CONVERT_BINDATA_CORE_TESTS: list[ConvertTest] = [
    ConvertTest(
        "bindata_from_int",
        input=42,
        to="binData",
        expected=struct.pack("<i", 42),
        msg="$convert should produce 4-byte binData from int",
    ),
    ConvertTest(
        "bindata_from_int_zero",
        input=0,
        to="binData",
        expected=struct.pack("<i", 0),
        msg="$convert should produce 4-byte binData from int 0",
    ),
    ConvertTest(
        "bindata_from_int_negative",
        input=-1,
        to="binData",
        expected=struct.pack("<i", -1),
        msg="$convert should produce 4-byte binData from negative int",
    ),
    ConvertTest(
        "bindata_from_long",
        input=Int64(42),
        to="binData",
        expected=struct.pack("<q", 42),
        msg="$convert should produce 8-byte binData from long",
    ),
    ConvertTest(
        "bindata_from_double",
        input=3.14,
        to="binData",
        expected=struct.pack("<d", 3.14),
        msg="$convert should produce 8-byte binData from double (IEEE 754)",
    ),
    ConvertTest(
        "bindata_from_bindata_identity",
        input=Binary(b"hello"),
        to="binData",
        expected=b"hello",
        msg="$convert should return same value for binData to binData with same subtype",
    ),
]

# Property [BinData String Formats]: string-to-binData conversion requires the
# format parameter and decodes format-specific input.
CONVERT_BINDATA_STRING_FORMAT_TESTS: list[ConvertTest] = [
    ConvertTest(
        "bindata_string_base64",
        input="Pj4+Pg==",
        to="binData",
        format="base64",
        expected=b">>>>",
        msg="$convert should decode base64 string to binData",
    ),
    ConvertTest(
        "bindata_string_base64url",
        input="Pj4-Pg",
        to="binData",
        format="base64url",
        expected=b">>>>",
        msg="$convert should decode base64url string with URL-safe chars and no padding to binData",
    ),
    ConvertTest(
        "bindata_string_utf8",
        input="hello",
        to="binData",
        format="utf8",
        expected=b"hello",
        msg="$convert should encode UTF-8 string to binData",
    ),
    ConvertTest(
        "bindata_string_hex",
        input="68656C6C6F",
        to="binData",
        format="hex",
        expected=b"hello",
        msg="$convert should decode hex string to binData",
    ),
    ConvertTest(
        "bindata_string_uuid",
        input="01020304-0506-0708-090a-0b0c0d0e0f10",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        expected=Binary(
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
            4,
        ),
        msg="$convert should decode UUID string to subtype 4 binData",
    ),
]

CONVERT_BINDATA_TESTS = (
    CONVERT_STRING_BINDATA_FORMAT_TESTS
    + CONVERT_BINDATA_CORE_TESTS
    + CONVERT_BINDATA_STRING_FORMAT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_BINDATA_TESTS))
def test_convert_bindata(collection, test_case: ConvertTest):
    """Test $convert BinData conversions."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
