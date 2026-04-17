from __future__ import annotations

from datetime import datetime, timezone

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
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR, INVALID_DOLLAR_FIELD_PATH
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Syntax Validation]: $convert requires an object argument. Non-object
# values produce a FailedToParse error.
CONVERT_SYNTAX_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "syntax_string",
        expr={"$convert": "hello"},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject string as argument",
    ),
    ConvertTest(
        "syntax_missing_field_ref",
        expr={"$convert": MISSING},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject missing field reference as argument",
    ),
    ConvertTest(
        "syntax_array",
        expr={"$convert": ["hello"]},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject array as argument",
    ),
    ConvertTest(
        "syntax_null",
        expr={"$convert": None},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject null as argument",
    ),
    ConvertTest(
        "syntax_int",
        expr={"$convert": 42},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject int as argument",
    ),
    ConvertTest(
        "syntax_bool",
        expr={"$convert": True},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject boolean as argument",
    ),
    ConvertTest(
        "syntax_double",
        expr={"$convert": 3.14},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject double as argument",
    ),
    ConvertTest(
        "syntax_long",
        expr={"$convert": Int64(42)},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Int64 as argument",
    ),
    ConvertTest(
        "syntax_decimal",
        expr={"$convert": Decimal128("42")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Decimal128 as argument",
    ),
    ConvertTest(
        "syntax_binary",
        expr={"$convert": Binary(b"data")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Binary as argument",
    ),
    ConvertTest(
        "syntax_date",
        expr={"$convert": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject datetime as argument",
    ),
    ConvertTest(
        "syntax_objectid",
        expr={"$convert": ObjectId("507f1f77bcf86cd799439011")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject ObjectId as argument",
    ),
    ConvertTest(
        "syntax_regex",
        expr={"$convert": Regex("pattern")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Regex as argument",
    ),
    ConvertTest(
        "syntax_timestamp",
        expr={"$convert": Timestamp(1, 1)},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Timestamp as argument",
    ),
    ConvertTest(
        "syntax_minkey",
        expr={"$convert": MinKey()},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject MinKey as argument",
    ),
    ConvertTest(
        "syntax_maxkey",
        expr={"$convert": MaxKey()},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject MaxKey as argument",
    ),
    ConvertTest(
        "syntax_code",
        expr={"$convert": Code("function() {}")},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Code as argument",
    ),
    ConvertTest(
        "syntax_code_scope",
        expr={"$convert": Code("function() {}", {"x": 1})},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject Code with scope as argument",
    ),
]

# Property [Missing Required Fields]: omitting 'input' or 'to' produces a
# FailedToParse error.
CONVERT_MISSING_FIELD_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "missing_both",
        expr={"$convert": {}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject empty object",
    ),
    ConvertTest(
        "missing_input",
        expr={"$convert": {"to": "int"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject missing input field",
    ),
    ConvertTest(
        "missing_to",
        expr={"$convert": {"input": 42}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject missing to field",
    ),
    ConvertTest(
        "missing_input_and_to_with_optionals",
        expr={"$convert": {"onError": "x", "onNull": "y"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject missing input and to even with optional fields",
    ),
]

# Property [Unknown Fields]: unrecognized field names in the $convert object
# produce a FailedToParse error. Field names are case-sensitive.
CONVERT_UNKNOWN_FIELD_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "unknown_field",
        expr={"$convert": {"input": 42, "to": "int", "unknown": 1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject unknown fields",
    ),
    ConvertTest(
        "case_Input",
        expr={"$convert": {"Input": 42, "to": "int"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject case-mismatched 'Input'",
    ),
    ConvertTest(
        "case_To",
        expr={"$convert": {"input": 42, "To": "int"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject case-mismatched 'To'",
    ),
    ConvertTest(
        "case_OnNull",
        expr={"$convert": {"input": 42, "to": "int", "OnNull": "x"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject case-mismatched 'OnNull'",
    ),
    ConvertTest(
        "case_OnError",
        expr={"$convert": {"input": 42, "to": "int", "OnError": "x"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject case-mismatched 'OnError'",
    ),
    ConvertTest(
        "case_Format",
        expr={"$convert": {"input": 42, "to": "int", "Format": "hex"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject case-mismatched 'Format'",
    ),
    ConvertTest(
        "case_ByteOrder",
        expr={"$convert": {"input": 42, "to": "int", "ByteOrder": "big"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject case-mismatched 'ByteOrder'",
    ),
    ConvertTest(
        "case_to_obj_Type",
        expr={"$convert": {"input": 42, "to": {"Type": "int"}}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject case-mismatched 'Type' in to object",
    ),
]

# Property [Dollar Sign Errors]: a bare "$" is rejected as an invalid field
# path and "$$" is rejected as an empty variable name in every string parameter.
CONVERT_DOLLAR_SIGN_ERROR_TESTS: list[ConvertTest] = [
    ConvertTest(
        "dollar_bare_input",
        input="$",
        to="int",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$convert should reject bare '$' as input field path",
    ),
    ConvertTest(
        "dollar_double_input",
        input="$$",
        to="int",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject '$$' as empty variable in input",
    ),
    ConvertTest(
        "dollar_bare_to",
        input=42,
        to="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$convert should reject bare '$' as to field path",
    ),
    ConvertTest(
        "dollar_double_to",
        input=42,
        to="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject '$$' as empty variable in to",
    ),
    ConvertTest(
        "dollar_bare_format",
        input=42,
        to="int",
        format="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$convert should reject bare '$' as format field path",
    ),
    ConvertTest(
        "dollar_double_format",
        input=42,
        to="int",
        format="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject '$$' as empty variable in format",
    ),
    ConvertTest(
        "dollar_bare_byte_order",
        input=42,
        to="int",
        byte_order="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$convert should reject bare '$' as byteOrder field path",
    ),
    ConvertTest(
        "dollar_double_byte_order",
        input=42,
        to="int",
        byte_order="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject '$$' as empty variable in byteOrder",
    ),
    ConvertTest(
        "dollar_bare_on_null",
        input=42,
        to="int",
        on_null="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$convert should reject bare '$' as onNull field path",
    ),
    ConvertTest(
        "dollar_double_on_null",
        input=42,
        to="int",
        on_null="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject '$$' as empty variable in onNull",
    ),
    ConvertTest(
        "dollar_bare_on_error",
        input=42,
        to="int",
        on_error="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$convert should reject bare '$' as onError field path",
    ),
    ConvertTest(
        "dollar_double_on_error",
        input=42,
        to="int",
        on_error="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$convert should reject '$$' as empty variable in onError",
    ),
]

CONVERT_INVALID_ARGS_TESTS = (
    CONVERT_SYNTAX_ERROR_TESTS
    + CONVERT_MISSING_FIELD_ERROR_TESTS
    + CONVERT_UNKNOWN_FIELD_ERROR_TESTS
    + CONVERT_DOLLAR_SIGN_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_INVALID_ARGS_TESTS))
def test_convert_invalid_args(collection, test_case: ConvertTest):
    """Test $convert invalid argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
