from __future__ import annotations

from datetime import datetime

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    CONVERT_BYTE_ORDER_TYPE_ERROR,
    CONVERT_BYTE_ORDER_VALUE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [ByteOrder Errors]: invalid 'byteOrder' parameter values produce
# specific error codes for wrong types or unrecognized strings.
CONVERT_BYTE_ORDER_ERROR_TESTS: list[ConvertTest] = [
    # Unrecognized byteOrder string values.
    ConvertTest(
        "byte_order_value_medium",
        input=42,
        to="binData",
        byte_order="medium",
        error_code=CONVERT_BYTE_ORDER_VALUE_ERROR,
        msg="$convert should reject unrecognized byteOrder 'medium'",
    ),
    ConvertTest(
        "byte_order_value_empty",
        input=42,
        to="binData",
        byte_order="",
        error_code=CONVERT_BYTE_ORDER_VALUE_ERROR,
        msg="$convert should reject empty string as byteOrder",
    ),
    ConvertTest(
        "byte_order_value_case_BIG",
        input=42,
        to="binData",
        byte_order="BIG",
        error_code=CONVERT_BYTE_ORDER_VALUE_ERROR,
        msg="$convert should reject case-mismatched byteOrder 'BIG'",
    ),
    # Wrong type for byteOrder.
    ConvertTest(
        "byte_order_type_int",
        input=42,
        to="binData",
        byte_order=42,
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject int as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_bool",
        input=42,
        to="binData",
        byte_order=True,
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject bool as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_array",
        input=42,
        to="binData",
        byte_order=[],
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject array as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_object",
        input=42,
        to="binData",
        byte_order={"a": 1},
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject object as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_double",
        input=42,
        to="binData",
        byte_order=42.5,
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject double as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_long",
        input=42,
        to="binData",
        byte_order=Int64(42),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject Int64 as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_decimal",
        input=42,
        to="binData",
        byte_order=Decimal128("42"),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject Decimal128 as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_binary",
        input=42,
        to="binData",
        byte_order=Binary(b"x"),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject Binary as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_objectid",
        input=42,
        to="binData",
        byte_order=ObjectId("507f1f77bcf86cd799439011"),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject ObjectId as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_datetime",
        input=42,
        to="binData",
        byte_order=datetime(2024, 1, 1),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject datetime as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_regex",
        input=42,
        to="binData",
        byte_order=Regex("abc"),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject Regex as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_code",
        input=42,
        to="binData",
        byte_order=Code("function(){}"),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject Code as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_timestamp",
        input=42,
        to="binData",
        byte_order=Timestamp(1, 1),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject Timestamp as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_minkey",
        input=42,
        to="binData",
        byte_order=MinKey(),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject MinKey as byteOrder",
    ),
    ConvertTest(
        "byte_order_type_maxkey",
        input=42,
        to="binData",
        byte_order=MaxKey(),
        error_code=CONVERT_BYTE_ORDER_TYPE_ERROR,
        msg="$convert should reject MaxKey as byteOrder",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_BYTE_ORDER_ERROR_TESTS))
def test_convert_byte_order_errors(collection, test_case: ConvertTest):
    """Test $convert byteOrder parameter errors."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
