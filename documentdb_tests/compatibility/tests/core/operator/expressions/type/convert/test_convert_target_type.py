from __future__ import annotations

import struct
from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Numeric Type Codes]: the to parameter accepts numeric BSON type
# codes as int32, Int64, whole-number double, and whole-number Decimal128.
CONVERT_NUMERIC_TYPE_CODE_TESTS: list[ConvertTest] = [
    ConvertTest(
        "type_code_int32_double",
        input=42,
        to=1,
        expected=42.0,
        msg="$convert should accept int32 type code 1 for double",
    ),
    ConvertTest(
        "type_code_int32_string",
        input=42,
        to=2,
        expected="42",
        msg="$convert should accept int32 type code 2 for string",
    ),
    ConvertTest(
        "type_code_int32_bindata",
        input="aGVsbG8=",
        to=5,
        format="base64",
        expected=b"hello",
        msg="$convert should accept int32 type code 5 for binData",
    ),
    ConvertTest(
        "type_code_int32_objectid",
        input="507f1f77bcf86cd799439011",
        to=7,
        expected=ObjectId("507f1f77bcf86cd799439011"),
        msg="$convert should accept int32 type code 7 for objectId",
    ),
    ConvertTest(
        "type_code_int32_bool",
        input=42,
        to=8,
        expected=True,
        msg="$convert should accept int32 type code 8 for bool",
    ),
    ConvertTest(
        "type_code_int32_date",
        input=INT64_ZERO,
        to=9,
        expected=datetime(1970, 1, 1, tzinfo=timezone.utc),
        msg="$convert should accept int32 type code 9 for date",
    ),
    ConvertTest(
        "type_code_int32_int",
        input=42,
        to=16,
        expected=42,
        msg="$convert should accept int32 type code 16 for int",
    ),
    ConvertTest(
        "type_code_int32_long",
        input=42,
        to=18,
        expected=Int64(42),
        msg="$convert should accept int32 type code 18 for long",
    ),
    ConvertTest(
        "type_code_int32_decimal",
        input=42,
        to=19,
        expected=Decimal128("42"),
        msg="$convert should accept int32 type code 19 for decimal",
    ),
    ConvertTest(
        "type_code_int64",
        input=42,
        to=Int64(16),
        expected=42,
        msg="$convert should accept Int64 type code for int",
    ),
    ConvertTest(
        "type_code_double",
        input=42,
        to=16.0,
        expected=42,
        msg="$convert should accept whole-number double type code for int",
    ),
    ConvertTest(
        "type_code_decimal128",
        input=42,
        to=Decimal128("16"),
        expected=42,
        msg="$convert should accept Decimal128 type code for int",
    ),
    ConvertTest(
        "type_code_decimal128_sci_notation",
        input=42,
        to=Decimal128("1.6E1"),
        expected=42,
        msg="$convert should accept Decimal128 scientific notation type code for int",
    ),
]

# Property [Object Form Type Identifier]: the object form {type: <name_or_code>}
# works for all target types and silently ignores extra fields.
CONVERT_OBJECT_FORM_TYPE_TESTS: list[ConvertTest] = [
    ConvertTest(
        "object_form_string_type",
        input=42,
        to={"type": "int"},
        expected=42,
        msg="$convert should accept object form with string type name",
    ),
    ConvertTest(
        "object_form_numeric_type",
        input=42,
        to={"type": 1},
        expected=42.0,
        msg="$convert should accept object form with numeric type code",
    ),
    ConvertTest(
        "object_form_extra_fields_ignored",
        input=42,
        to={"type": "int", "extra": "ignored"},
        expected=42,
        msg="$convert should silently ignore extra fields in object form",
    ),
    ConvertTest(
        "object_form_case_mismatched_subtype_ignored",
        input=42,
        to={"type": "binData", "Subtype": 5},
        expected=struct.pack("<i", 42),
        msg="$convert should ignore case-mismatched 'Subtype' in object form",
    ),
]

CONVERT_TARGET_TYPE_SUCCESS_TESTS = CONVERT_NUMERIC_TYPE_CODE_TESTS + CONVERT_OBJECT_FORM_TYPE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_TARGET_TYPE_SUCCESS_TESTS))
def test_convert_target_type(collection, test_case: ConvertTest):
    """Test $convert target type identifiers."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
