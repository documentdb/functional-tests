from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    TRIM_MISSING_INPUT_ERROR,
    TRIM_UNKNOWN_FIELD_ERROR,
    TRIM_WRONG_TYPE_ERROR,
)
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF
from documentdb_tests.compatibility.tests.core.operator.expressions.string.rtrim.utils.rtrim_common import (
    RtrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Syntax Validation]: invalid $rtrim object shapes produce errors.
RTRIM_SYNTAX_ERROR_TESTS: list[RtrimTest] = [
    # Non-document arguments produce TRIM_WRONG_TYPE_ERROR.
    RtrimTest(
        "syntax_string",
        expr={"$rtrim": "hello"},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject string as argument",
    ),
    RtrimTest(
        "syntax_array",
        expr={"$rtrim": ["hello"]},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject array as argument",
    ),
    RtrimTest(
        "syntax_null",
        expr={"$rtrim": None},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject null as argument",
    ),
    RtrimTest(
        "syntax_int",
        expr={"$rtrim": 42},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject int as argument",
    ),
    RtrimTest(
        "syntax_bool",
        expr={"$rtrim": True},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject boolean as argument",
    ),
    RtrimTest(
        "syntax_float",
        expr={"$rtrim": 3.14},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject float as argument",
    ),
    RtrimTest(
        "syntax_long",
        expr={"$rtrim": Int64(42)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject Int64 as argument",
    ),
    RtrimTest(
        "syntax_binary",
        expr={"$rtrim": Binary(b"data")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject Binary as argument",
    ),
    RtrimTest(
        "syntax_binary_uuid",
        expr={"$rtrim": Binary(b"data", 4)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject Binary UUID as argument",
    ),
    RtrimTest(
        "syntax_date",
        expr={"$rtrim": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject datetime as argument",
    ),
    RtrimTest(
        "syntax_decimal128",
        expr={"$rtrim": DECIMAL128_ONE_AND_HALF},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject Decimal128 as argument",
    ),
    RtrimTest(
        "syntax_maxkey",
        expr={"$rtrim": MaxKey()},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject MaxKey as argument",
    ),
    RtrimTest(
        "syntax_minkey",
        expr={"$rtrim": MinKey()},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject MinKey as argument",
    ),
    RtrimTest(
        "syntax_objectid",
        expr={"$rtrim": ObjectId("507f1f77bcf86cd799439011")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject ObjectId as argument",
    ),
    RtrimTest(
        "syntax_regex",
        expr={"$rtrim": Regex("pattern")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject Regex as argument",
    ),
    RtrimTest(
        "syntax_timestamp",
        expr={"$rtrim": Timestamp(1, 1)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject Timestamp as argument",
    ),
    RtrimTest(
        "syntax_code",
        expr={"$rtrim": Code("function() {}")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject Code as argument",
    ),
    RtrimTest(
        "syntax_code_scope",
        expr={"$rtrim": Code("function() {}", {"x": 1})},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$rtrim should reject Code with scope as argument",
    ),
    # Omitting input entirely.
    RtrimTest(
        "syntax_no_input",
        expr={"$rtrim": {"chars": "a"}},
        error_code=TRIM_MISSING_INPUT_ERROR,
        msg="$rtrim should require the input field",
    ),
    # Empty object.
    RtrimTest(
        "syntax_empty_object",
        expr={"$rtrim": {}},
        error_code=TRIM_MISSING_INPUT_ERROR,
        msg="$rtrim should reject empty object",
    ),
    # Unknown extra field.
    RtrimTest(
        "syntax_unknown_field",
        expr={"$rtrim": {"input": "hello", "unknown": 1}},
        error_code=TRIM_UNKNOWN_FIELD_ERROR,
        msg="$rtrim should reject unknown fields in the argument object",
    ),
    # Case-sensitive field names.
    RtrimTest(
        "syntax_case_sensitive_field",
        expr={"$rtrim": {"Input": "hello"}},
        error_code=TRIM_UNKNOWN_FIELD_ERROR,
        msg="$rtrim should reject case-mismatched field name 'Input'",
    ),
]

# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
RTRIM_DOLLAR_SIGN_ERROR_TESTS: list[RtrimTest] = [
    RtrimTest(
        "dollar_bare_input",
        input="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$rtrim should reject bare '$' as input field path",
    ),
    RtrimTest(
        "dollar_bare_chars",
        input="hello",
        chars="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$rtrim should reject bare '$' as chars field path",
    ),
    RtrimTest(
        "dollar_double_input",
        input="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$rtrim should reject '$$' as empty variable name in input",
    ),
    RtrimTest(
        "dollar_double_chars",
        input="hello",
        chars="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$rtrim should reject '$$' as empty variable name in chars",
    ),
]

RTRIM_INVALID_ARGS_ALL_TESTS = RTRIM_SYNTAX_ERROR_TESTS + RTRIM_DOLLAR_SIGN_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_INVALID_ARGS_ALL_TESTS))
def test_rtrim_invalid_args(collection, test_case: RtrimTest):
    """Test $rtrim syntax validation and dollar sign errors."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
