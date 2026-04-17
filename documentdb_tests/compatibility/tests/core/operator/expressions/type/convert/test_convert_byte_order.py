from __future__ import annotations

import struct
from datetime import datetime

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

# Property [byteOrder Default]: omitting byteOrder or specifying "little"
# produces identical little-endian byte ordering for numeric-to-binData and
# binData-to-numeric conversions.
CONVERT_BYTE_ORDER_DEFAULT_TESTS: list[ConvertTest] = [
    ConvertTest(
        "byte_order_omitted_int",
        input=99,
        to="binData",
        expected=struct.pack("<i", 99),
        msg="$convert should default to little-endian when byteOrder is omitted",
    ),
    ConvertTest(
        "byte_order_explicit_little_int",
        input=99,
        to="binData",
        byte_order="little",
        expected=struct.pack("<i", 99),
        msg="$convert with explicit byteOrder little should match default for int to binData",
    ),
    ConvertTest(
        "byte_order_null_defaults_to_little",
        input=99,
        to="binData",
        byte_order=None,
        expected=struct.pack("<i", 99),
        msg="$convert should treat null byteOrder as default little-endian",
    ),
    ConvertTest(
        "byte_order_explicit_little_long",
        input=Int64(42),
        to="binData",
        byte_order="little",
        expected=struct.pack("<q", 42),
        msg="$convert with explicit byteOrder little should match default for long to binData",
    ),
    ConvertTest(
        "byte_order_explicit_little_double",
        input=42.0,
        to="binData",
        byte_order="little",
        expected=struct.pack("<d", 42.0),
        msg="$convert with explicit byteOrder little should match default for double to binData",
    ),
    ConvertTest(
        "byte_order_explicit_little_bindata_to_int",
        input=Binary(struct.pack("<i", 42)),
        to="int",
        byte_order="little",
        expected=42,
        msg="$convert with explicit byteOrder little should match default for binData to int",
    ),
]

# Property [byteOrder Big Endian]: specifying byteOrder "big" places the most
# significant byte first for numeric-to-binData and binData-to-numeric
# conversions.
CONVERT_BYTE_ORDER_BIG_TESTS: list[ConvertTest] = [
    ConvertTest(
        "byte_order_big_int_to_bindata",
        input=42,
        to="binData",
        byte_order="big",
        expected=struct.pack(">i", 42),
        msg="$convert should produce big-endian binData from int",
    ),
    ConvertTest(
        "byte_order_big_long_to_bindata",
        input=Int64(42),
        to="binData",
        byte_order="big",
        expected=struct.pack(">q", 42),
        msg="$convert should produce big-endian binData from long",
    ),
    ConvertTest(
        "byte_order_big_double_to_bindata",
        input=42.0,
        to="binData",
        byte_order="big",
        expected=struct.pack(">d", 42.0),
        msg="$convert should produce big-endian binData from double",
    ),
    ConvertTest(
        "byte_order_big_bindata_to_int",
        input=Binary(struct.pack(">i", 42)),
        to="int",
        byte_order="big",
        expected=42,
        msg="$convert should interpret big-endian binData as int",
    ),
    ConvertTest(
        "byte_order_big_bindata_to_long",
        input=Binary(struct.pack(">q", 42)),
        to="long",
        byte_order="big",
        expected=Int64(42),
        msg="$convert should interpret big-endian binData as long",
    ),
    ConvertTest(
        "byte_order_big_bindata_to_double",
        input=Binary(struct.pack(">d", 42.0)),
        to="double",
        byte_order="big",
        expected=42.0,
        msg="$convert should interpret big-endian binData as double",
    ),
]

# Property [byteOrder Ignored for Non-Numeric-BinData]: byteOrder is silently
# ignored for conversions that do not involve numeric-to-binData or
# binData-to-numeric paths.
CONVERT_BYTE_ORDER_IGNORED_TESTS: list[ConvertTest] = [
    ConvertTest(
        "byte_order_ignored_string_to_int",
        input="42",
        to="int",
        byte_order="big",
        expected=42,
        msg="$convert should ignore byteOrder for string to int",
    ),
    ConvertTest(
        "byte_order_ignored_string_to_long",
        input="42",
        to="long",
        byte_order="big",
        expected=Int64(42),
        msg="$convert should ignore byteOrder for string to long",
    ),
    ConvertTest(
        "byte_order_ignored_int_to_double",
        input=42,
        to="double",
        byte_order="big",
        expected=42.0,
        msg="$convert should ignore byteOrder for int to double",
    ),
    ConvertTest(
        "byte_order_ignored_int_to_decimal",
        input=42,
        to="decimal",
        byte_order="big",
        expected=Decimal128("42"),
        msg="$convert should ignore byteOrder for int to decimal",
    ),
    ConvertTest(
        "byte_order_ignored_int_to_string",
        input=42,
        to="string",
        byte_order="big",
        expected="42",
        msg="$convert should ignore byteOrder for int to string",
    ),
    ConvertTest(
        "byte_order_ignored_int_to_bool",
        input=42,
        to="bool",
        byte_order="big",
        expected=True,
        msg="$convert should ignore byteOrder for int to bool",
    ),
    ConvertTest(
        "byte_order_ignored_string_to_date",
        input="2024-06-15T12:30:45Z",
        to="date",
        byte_order="big",
        expected=datetime(2024, 6, 15, 12, 30, 45),
        msg="$convert should ignore byteOrder for string to date",
    ),
    ConvertTest(
        "byte_order_ignored_string_to_objectId",
        input="507f1f77bcf86cd799439011",
        to="objectId",
        byte_order="big",
        expected=ObjectId("507f1f77bcf86cd799439011"),
        msg="$convert should ignore byteOrder for string to objectId",
    ),
    ConvertTest(
        "byte_order_ignored_string_to_bindata_utf8",
        input="hello",
        to="binData",
        byte_order="big",
        format="utf8",
        expected=b"hello",
        msg="$convert should ignore byteOrder for string to binData with format",
    ),
]

CONVERT_BYTE_ORDER_SUCCESS_TESTS = (
    CONVERT_BYTE_ORDER_DEFAULT_TESTS
    + CONVERT_BYTE_ORDER_BIG_TESTS
    + CONVERT_BYTE_ORDER_IGNORED_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_BYTE_ORDER_SUCCESS_TESTS))
def test_convert_byte_order(collection, test_case: ConvertTest):
    """Test $convert byteOrder behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
