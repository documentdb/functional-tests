from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [BinData Conversion Errors]: input types not in the accepted set for
# binData produce a conversion failure error.
CONVERT_BINDATA_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "bindata_err_bool",
        input=True,
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject bool to binData",
    ),
    ConvertTest(
        "bindata_err_decimal",
        input=Decimal128("42"),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject Decimal128 to binData",
    ),
    ConvertTest(
        "bindata_err_date",
        input=datetime(2024, 1, 1, tzinfo=timezone.utc),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject date to binData",
    ),
    ConvertTest(
        "bindata_err_objectid",
        input=ObjectId("507f1f77bcf86cd799439011"),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject ObjectId to binData",
    ),
    ConvertTest(
        "bindata_err_regex",
        input=Regex("abc"),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject Regex to binData",
    ),
    ConvertTest(
        "bindata_err_array",
        input=[1, 2],
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject array to binData",
    ),
    ConvertTest(
        "bindata_err_object",
        input={"key": "val"},
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject object to binData",
    ),
    ConvertTest(
        "bindata_err_code",
        input=Code("function(){}"),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject Code to binData",
    ),
    ConvertTest(
        "bindata_err_code_with_scope",
        input=Code("function(){}", {}),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject Code with scope to binData",
    ),
    ConvertTest(
        "bindata_err_minkey",
        input=MinKey(),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject MinKey to binData",
    ),
    ConvertTest(
        "bindata_err_maxkey",
        input=MaxKey(),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject MaxKey to binData",
    ),
    ConvertTest(
        "bindata_err_timestamp",
        input=Timestamp(1, 1),
        to="binData",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject Timestamp to binData",
    ),
]

# Property [Cross-Subtype BinData Errors]: converting BinData to BinData with a
# different subtype produces a conversion failure error.
CONVERT_CROSS_SUBTYPE_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "cross_subtype_err_3_to_0",
        input=Binary(b"\x01\x02", 3),
        to={"type": "binData", "subtype": 0},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject BinData subtype 3 to subtype 0",
    ),
    ConvertTest(
        "cross_subtype_err_0_to_4",
        input=Binary(b"\x01\x02", 0),
        to={"type": "binData", "subtype": 4},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject BinData subtype 0 to subtype 4",
    ),
    ConvertTest(
        "cross_subtype_err_128_to_0",
        input=Binary(b"\x01\x02", 128),
        to={"type": "binData", "subtype": 0},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject BinData subtype 128 to subtype 0",
    ),
]

# Property [BinData Format Conversion Errors]: invalid string inputs for format
# conversions produce a conversion failure error.
CONVERT_BINDATA_FORMAT_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "bindata_fmt_err_auto_string_to_bindata",
        input="aGVsbG8=",
        to="binData",
        format="auto",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject auto format for string to binData",
    ),
    ConvertTest(
        "bindata_fmt_err_base64_no_padding",
        input="aGVsbG8",
        to="binData",
        format="base64",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject base64 string without padding",
    ),
    ConvertTest(
        "bindata_fmt_err_base64url_chars_in_base64",
        input="aGVs-G8=",
        to="binData",
        format="base64",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject base64url characters in base64 input",
    ),
    ConvertTest(
        "bindata_fmt_err_base64_chars_in_base64url",
        input="aGVs+G8",
        to="binData",
        format="base64url",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject base64 characters in base64url input",
    ),
    ConvertTest(
        "bindata_fmt_err_hex_odd_length",
        input="abc",
        to="binData",
        format="hex",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject odd-length hex string",
    ),
    ConvertTest(
        "bindata_fmt_err_hex_invalid_char",
        input="GG",
        to="binData",
        format="hex",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject invalid hex character",
    ),
    ConvertTest(
        "bindata_fmt_err_uuid_non_subtype_4",
        input="550e8400-e29b-41d4-a716-446655440000",
        to={"type": "binData", "subtype": 0},
        format="uuid",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject uuid format with non-4 subtype",
    ),
    ConvertTest(
        "bindata_fmt_err_subtype_4_non_uuid_format",
        input="aGVsbG8=",
        to={"type": "binData", "subtype": 4},
        format="base64",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject non-uuid format with subtype 4",
    ),
    ConvertTest(
        "bindata_fmt_err_invalid_uuid_string",
        input="not-a-uuid",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject invalid uuid string",
    ),
    ConvertTest(
        "bindata_fmt_err_base64_invalid",
        input="not-base64!",
        to="binData",
        format="base64",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject invalid base64 string",
    ),
    ConvertTest(
        "bindata_fmt_err_base64url_invalid",
        input="not!valid",
        to="binData",
        format="base64url",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject invalid base64url string",
    ),
    ConvertTest(
        "bindata_fmt_err_uuid_truncated",
        input="550e8400-e29b-41d4-a716",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject truncated uuid string",
    ),
    ConvertTest(
        "bindata_fmt_err_uuid_no_dashes",
        input="550e8400e29b41d4a716446655440000",
        to={"type": "binData", "subtype": 4},
        format="uuid",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject uuid string without dashes",
    ),
    # 0x80 is an invalid UTF-8 start byte.
    ConvertTest(
        "bindata_fmt_err_utf8_invalid_bytes",
        input=Binary(b"\x80\xc0\x00"),
        to="string",
        format="utf8",
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject BinData with invalid UTF-8 byte sequence",
    ),
]

CONVERT_BINDATA_ALL_ERROR_TESTS = (
    CONVERT_BINDATA_ERROR_TESTS
    + CONVERT_CROSS_SUBTYPE_ERROR_TESTS
    + CONVERT_BINDATA_FORMAT_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_BINDATA_ALL_ERROR_TESTS))
def test_convert_bindata_errors(collection, test_case: ConvertTest):
    """Test $convert BinData conversion errors."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
