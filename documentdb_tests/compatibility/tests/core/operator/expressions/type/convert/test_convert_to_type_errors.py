from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
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
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONVERSION_FAILURE_ERROR,
    CONVERT_SUBTYPE_INVALID_RANGE_ERROR,
    CONVERT_SUBTYPE_NOT_INTEGER_ERROR,
    CONVERT_SUBTYPE_TYPE_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [to Type Errors]: the 'to' parameter rejects wrong BSON types,
# unrecognized type names, and malformed object forms.
CONVERT_TO_TYPE_ERROR_TESTS: list[ConvertTest] = [
    # Wrong BSON type for 'to' (not string, number, or object).
    ConvertTest(
        "to_type_bool",
        input=42,
        to=True,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject bool as to parameter",
    ),
    ConvertTest(
        "to_type_array",
        input=42,
        to=[],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject array as to parameter",
    ),
    ConvertTest(
        "to_type_binary",
        input=42,
        to=Binary(b"x"),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Binary as to parameter",
    ),
    ConvertTest(
        "to_type_objectid",
        input=42,
        to=ObjectId("507f1f77bcf86cd799439011"),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject ObjectId as to parameter",
    ),
    ConvertTest(
        "to_type_datetime",
        input=42,
        to=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject datetime as to parameter",
    ),
    ConvertTest(
        "to_type_regex",
        input=42,
        to=Regex("abc"),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Regex as to parameter",
    ),
    ConvertTest(
        "to_type_code",
        input=42,
        to=Code("function(){}"),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Code as to parameter",
    ),
    ConvertTest(
        "to_type_timestamp",
        input=42,
        to=Timestamp(1, 1),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Timestamp as to parameter",
    ),
    ConvertTest(
        "to_type_minkey",
        input=42,
        to=MinKey(),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject MinKey as to parameter",
    ),
    ConvertTest(
        "to_type_maxkey",
        input=42,
        to=MaxKey(),
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject MaxKey as to parameter",
    ),
    # Unrecognized string type names.
    ConvertTest(
        "to_name_integer",
        input=42,
        to="integer",
        error_code=BAD_VALUE_ERROR,
        msg="$convert should reject unrecognized type name 'integer'",
    ),
    ConvertTest(
        "to_name_str",
        input=42,
        to="str",
        error_code=BAD_VALUE_ERROR,
        msg="$convert should reject unrecognized type name 'str'",
    ),
    ConvertTest(
        "to_name_empty",
        input=42,
        to="",
        error_code=BAD_VALUE_ERROR,
        msg="$convert should reject empty string as type name",
    ),
    ConvertTest(
        "to_name_case_BOOL",
        input=42,
        to="BOOL",
        error_code=BAD_VALUE_ERROR,
        msg="$convert should reject case-mismatched type name 'BOOL'",
    ),
    # Numeric codes that don't map to a BSON type.
    ConvertTest(
        "to_code_99",
        input=42,
        to=99,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject numeric type code 99",
    ),
    ConvertTest(
        "to_code_255",
        input=42,
        to=255,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject numeric type code 255",
    ),
    # Numeric codes that map to recognized but unsupported target types.
    ConvertTest(
        "to_code_0_missing",
        input=42,
        to=0,
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject numeric type code 0 (missing)",
    ),
    ConvertTest(
        "to_code_neg1_minkey",
        input=42,
        to=-1,
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject numeric type code -1 (minKey)",
    ),
    ConvertTest(
        "to_code_3_object",
        input=42,
        to=3,
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject numeric type code 3 (object)",
    ),
    ConvertTest(
        "to_code_4_array",
        input=42,
        to=4,
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$convert should reject numeric type code 4 (array)",
    ),
    # Object form with missing 'type' field.
    ConvertTest(
        "to_obj_missing_type",
        input=42,
        to={"subtype": 5},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject object form without 'type' field",
    ),
    # Object form with wrong type for 'type' field.
    ConvertTest(
        "to_obj_type_null",
        input=42,
        to={"type": None},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject null as type in object form",
    ),
    ConvertTest(
        "to_obj_type_bool",
        input=42,
        to={"type": True},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject bool as type in object form",
    ),
    ConvertTest(
        "to_obj_type_array",
        input=42,
        to={"type": []},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject array as type in object form",
    ),
    ConvertTest(
        "to_obj_type_binary",
        input=42,
        to={"type": Binary(b"x")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Binary as type in object form",
    ),
    ConvertTest(
        "to_obj_type_objectid",
        input=42,
        to={"type": ObjectId("507f1f77bcf86cd799439011")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject ObjectId as type in object form",
    ),
    ConvertTest(
        "to_obj_type_datetime",
        input=42,
        to={"type": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject datetime as type in object form",
    ),
    ConvertTest(
        "to_obj_type_regex",
        input=42,
        to={"type": Regex("abc")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Regex as type in object form",
    ),
    ConvertTest(
        "to_obj_type_code",
        input=42,
        to={"type": Code("function(){}")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Code as type in object form",
    ),
    ConvertTest(
        "to_obj_type_timestamp",
        input=42,
        to={"type": Timestamp(1, 1)},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Timestamp as type in object form",
    ),
    ConvertTest(
        "to_obj_type_minkey",
        input=42,
        to={"type": MinKey()},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject MinKey as type in object form",
    ),
    ConvertTest(
        "to_obj_type_maxkey",
        input=42,
        to={"type": MaxKey()},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject MaxKey as type in object form",
    ),
    ConvertTest(
        "to_obj_type_unrecognized_code",
        input=42,
        to={"type": 42},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject unrecognized numeric code in object form type",
    ),
]

# Property [Subtype Errors]: invalid to.subtype values produce specific error
# codes for non-integer, out-of-range, or wrong-type values.
CONVERT_SUBTYPE_ERROR_TESTS: list[ConvertTest] = [
    # Non-integer numeric values.
    ConvertTest(
        "subtype_fractional_double",
        input=42,
        to={"type": "binData", "subtype": 1.5},
        error_code=CONVERT_SUBTYPE_NOT_INTEGER_ERROR,
        msg="$convert should reject fractional double as subtype",
    ),
    ConvertTest(
        "subtype_fractional_decimal",
        input=42,
        to={"type": "binData", "subtype": DECIMAL128_ONE_AND_HALF},
        error_code=CONVERT_SUBTYPE_NOT_INTEGER_ERROR,
        msg="$convert should reject fractional Decimal128 as subtype",
    ),
    ConvertTest(
        "subtype_nan",
        input=42,
        to={"type": "binData", "subtype": FLOAT_NAN},
        error_code=CONVERT_SUBTYPE_NOT_INTEGER_ERROR,
        msg="$convert should reject NaN as subtype",
    ),
    ConvertTest(
        "subtype_infinity",
        input=42,
        to={"type": "binData", "subtype": FLOAT_INFINITY},
        error_code=CONVERT_SUBTYPE_NOT_INTEGER_ERROR,
        msg="$convert should reject Infinity as subtype",
    ),
    # Out-of-range integer values.
    ConvertTest(
        "subtype_negative",
        input=42,
        to={"type": "binData", "subtype": -1},
        error_code=CONVERT_SUBTYPE_INVALID_RANGE_ERROR,
        msg="$convert should reject negative subtype",
    ),
    ConvertTest(
        "subtype_256",
        input=42,
        to={"type": "binData", "subtype": 256},
        error_code=CONVERT_SUBTYPE_INVALID_RANGE_ERROR,
        msg="$convert should reject subtype 256",
    ),
    ConvertTest(
        "subtype_10_gap",
        input=42,
        to={"type": "binData", "subtype": 10},
        error_code=CONVERT_SUBTYPE_INVALID_RANGE_ERROR,
        msg="$convert should reject subtype 10 (in 10-127 gap)",
    ),
    ConvertTest(
        "subtype_127_gap",
        input=42,
        to={"type": "binData", "subtype": 127},
        error_code=CONVERT_SUBTYPE_INVALID_RANGE_ERROR,
        msg="$convert should reject subtype 127 (in 10-127 gap)",
    ),
    # Wrong type entirely.
    ConvertTest(
        "subtype_type_string",
        input=42,
        to={"type": "binData", "subtype": "five"},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject string as subtype",
    ),
    ConvertTest(
        "subtype_type_bool",
        input=42,
        to={"type": "binData", "subtype": True},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject bool as subtype",
    ),
    ConvertTest(
        "subtype_type_null",
        input=42,
        to={"type": "binData", "subtype": None},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject null as subtype",
    ),
    ConvertTest(
        "subtype_type_array",
        input=42,
        to={"type": "binData", "subtype": []},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject array as subtype",
    ),
    ConvertTest(
        "subtype_type_object",
        input=42,
        to={"type": "binData", "subtype": {"a": 1}},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject object as subtype",
    ),
    ConvertTest(
        "subtype_type_binary",
        input=42,
        to={"type": "binData", "subtype": Binary(b"x")},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject Binary as subtype",
    ),
    ConvertTest(
        "subtype_type_objectid",
        input=42,
        to={"type": "binData", "subtype": ObjectId("507f1f77bcf86cd799439011")},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject ObjectId as subtype",
    ),
    ConvertTest(
        "subtype_type_datetime",
        input=42,
        to={"type": "binData", "subtype": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject datetime as subtype",
    ),
    ConvertTest(
        "subtype_type_regex",
        input=42,
        to={"type": "binData", "subtype": Regex("abc")},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject Regex as subtype",
    ),
    ConvertTest(
        "subtype_type_code",
        input=42,
        to={"type": "binData", "subtype": Code("function(){}")},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject Code as subtype",
    ),
    ConvertTest(
        "subtype_type_timestamp",
        input=42,
        to={"type": "binData", "subtype": Timestamp(1, 1)},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject Timestamp as subtype",
    ),
    ConvertTest(
        "subtype_type_minkey",
        input=42,
        to={"type": "binData", "subtype": MinKey()},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject MinKey as subtype",
    ),
    ConvertTest(
        "subtype_type_maxkey",
        input=42,
        to={"type": "binData", "subtype": MaxKey()},
        error_code=CONVERT_SUBTYPE_TYPE_ERROR,
        msg="$convert should reject MaxKey as subtype",
    ),
]

CONVERT_TO_TYPE_ALL_ERROR_TESTS = CONVERT_TO_TYPE_ERROR_TESTS + CONVERT_SUBTYPE_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_TO_TYPE_ALL_ERROR_TESTS))
def test_convert_to_type_errors(collection, test_case: ConvertTest):
    """Test $convert to type and subtype errors."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
