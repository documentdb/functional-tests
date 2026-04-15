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
    CONVERT_FORMAT_TYPE_ERROR,
    CONVERT_FORMAT_VALUE_ERROR,
    CONVERT_MISSING_FORMAT_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Format Errors]: invalid 'format' parameter values produce specific
# error codes for wrong types or unrecognized strings.
CONVERT_FORMAT_ERROR_TESTS: list[ConvertTest] = [
    # Unrecognized format string values.
    ConvertTest(
        "format_value_xml",
        input="hello",
        to="binData",
        format="xml",
        error_code=CONVERT_FORMAT_VALUE_ERROR,
        msg="$convert should reject unrecognized format 'xml'",
    ),
    ConvertTest(
        "format_value_empty",
        input="hello",
        to="binData",
        format="",
        error_code=CONVERT_FORMAT_VALUE_ERROR,
        msg="$convert should reject empty string as format",
    ),
    ConvertTest(
        "format_value_case_BASE64",
        input="hello",
        to="binData",
        format="BASE64",
        error_code=CONVERT_FORMAT_VALUE_ERROR,
        msg="$convert should reject case-mismatched format 'BASE64'",
    ),
    # Wrong type for format.
    ConvertTest(
        "format_type_int",
        input="hello",
        to="binData",
        format=42,
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject int as format",
    ),
    ConvertTest(
        "format_type_bool",
        input="hello",
        to="binData",
        format=True,
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject bool as format",
    ),
    ConvertTest(
        "format_type_array",
        input="hello",
        to="binData",
        format=[],
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject array as format",
    ),
    ConvertTest(
        "format_type_object",
        input="hello",
        to="binData",
        format={"a": 1},
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject object as format",
    ),
    ConvertTest(
        "format_type_binary",
        input="hello",
        to="binData",
        format=Binary(b"x"),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject Binary as format",
    ),
    ConvertTest(
        "format_type_double",
        input="hello",
        to="binData",
        format=42.5,
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject double as format",
    ),
    ConvertTest(
        "format_type_long",
        input="hello",
        to="binData",
        format=Int64(42),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject Int64 as format",
    ),
    ConvertTest(
        "format_type_decimal",
        input="hello",
        to="binData",
        format=Decimal128("42"),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject Decimal128 as format",
    ),
    ConvertTest(
        "format_type_objectid",
        input="hello",
        to="binData",
        format=ObjectId("507f1f77bcf86cd799439011"),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject ObjectId as format",
    ),
    ConvertTest(
        "format_type_datetime",
        input="hello",
        to="binData",
        format=datetime(2024, 1, 1),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject datetime as format",
    ),
    ConvertTest(
        "format_type_regex",
        input="hello",
        to="binData",
        format=Regex("abc"),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject Regex as format",
    ),
    ConvertTest(
        "format_type_code",
        input="hello",
        to="binData",
        format=Code("function(){}"),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject Code as format",
    ),
    ConvertTest(
        "format_type_timestamp",
        input="hello",
        to="binData",
        format=Timestamp(1, 1),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject Timestamp as format",
    ),
    ConvertTest(
        "format_type_minkey",
        input="hello",
        to="binData",
        format=MinKey(),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject MinKey as format",
    ),
    ConvertTest(
        "format_type_maxkey",
        input="hello",
        to="binData",
        format=MaxKey(),
        error_code=CONVERT_FORMAT_TYPE_ERROR,
        msg="$convert should reject MaxKey as format",
    ),
    # Null format falls through to missing-format error.
    ConvertTest(
        "format_null_treated_as_missing",
        input="hello",
        to="binData",
        format=None,
        error_code=CONVERT_MISSING_FORMAT_ERROR,
        msg="$convert should treat null format as missing for string to binData",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_FORMAT_ERROR_TESTS))
def test_convert_format_errors(collection, test_case: ConvertTest):
    """Test $convert format parameter errors."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
