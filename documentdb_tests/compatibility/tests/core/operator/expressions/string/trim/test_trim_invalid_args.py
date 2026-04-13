from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    TRIM_MISSING_INPUT_ERROR,
    TRIM_UNKNOWN_FIELD_ERROR,
    TRIM_WRONG_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

from .utils.trim_common import (
    TrimTest,
    _expr,
)

# Property [Syntax Validation]: invalid $trim object shapes produce errors.
TRIM_SYNTAX_ERROR_TESTS: list[TrimTest] = [
    # Non-document arguments produce TRIM_WRONG_TYPE_ERROR.
    TrimTest(
        "syntax_string",
        expr={"$trim": "hello"},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject string as argument",
    ),
    TrimTest(
        "syntax_array",
        expr={"$trim": ["hello"]},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject array as argument",
    ),
    TrimTest(
        "syntax_null",
        expr={"$trim": None},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject null as argument",
    ),
    TrimTest(
        "syntax_int",
        expr={"$trim": 42},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject int as argument",
    ),
    TrimTest(
        "syntax_bool",
        expr={"$trim": True},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject boolean as argument",
    ),
    TrimTest(
        "syntax_float",
        expr={"$trim": 3.14},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject float as argument",
    ),
    TrimTest(
        "syntax_long",
        expr={"$trim": Int64(42)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject Int64 as argument",
    ),
    TrimTest(
        "syntax_binary",
        expr={"$trim": Binary(b"data")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject Binary as argument",
    ),
    TrimTest(
        "syntax_binary_uuid",
        expr={"$trim": Binary(b"data", 4)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject Binary UUID as argument",
    ),
    TrimTest(
        "syntax_date",
        expr={"$trim": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject datetime as argument",
    ),
    TrimTest(
        "syntax_decimal128",
        expr={"$trim": DECIMAL128_ONE_AND_HALF},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject Decimal128 as argument",
    ),
    TrimTest(
        "syntax_maxkey",
        expr={"$trim": MaxKey()},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject MaxKey as argument",
    ),
    TrimTest(
        "syntax_minkey",
        expr={"$trim": MinKey()},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject MinKey as argument",
    ),
    TrimTest(
        "syntax_objectid",
        expr={"$trim": ObjectId("507f1f77bcf86cd799439011")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject ObjectId as argument",
    ),
    TrimTest(
        "syntax_regex",
        expr={"$trim": Regex("pattern")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject Regex as argument",
    ),
    TrimTest(
        "syntax_timestamp",
        expr={"$trim": Timestamp(1, 1)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject Timestamp as argument",
    ),
    TrimTest(
        "syntax_code",
        expr={"$trim": Code("function() {}")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject Code as argument",
    ),
    TrimTest(
        "syntax_code_scope",
        expr={"$trim": Code("function() {}", {"x": 1})},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$trim should reject Code with scope as argument",
    ),
    # Omitting input entirely.
    TrimTest(
        "syntax_no_input",
        expr={"$trim": {"chars": "a"}},
        error_code=TRIM_MISSING_INPUT_ERROR,
        msg="$trim should require the input field",
    ),
    # Empty object.
    TrimTest(
        "syntax_empty_object",
        expr={"$trim": {}},
        error_code=TRIM_MISSING_INPUT_ERROR,
        msg="$trim should reject empty object",
    ),
    # Unknown extra field.
    TrimTest(
        "syntax_unknown_field",
        expr={"$trim": {"input": "hello", "unknown": 1}},
        error_code=TRIM_UNKNOWN_FIELD_ERROR,
        msg="$trim should reject unknown fields in the argument object",
    ),
    # Case-sensitive field names.
    TrimTest(
        "syntax_case_sensitive_field",
        expr={"$trim": {"Input": "hello"}},
        error_code=TRIM_UNKNOWN_FIELD_ERROR,
        msg="$trim should reject case-mismatched field name 'Input'",
    ),
]

# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
TRIM_DOLLAR_SIGN_ERROR_TESTS: list[TrimTest] = [
    TrimTest(
        "dollar_bare_input",
        input="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$trim should reject bare '$' as input field path",
    ),
    TrimTest(
        "dollar_bare_chars",
        input="hello",
        chars="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$trim should reject bare '$' as chars field path",
    ),
    TrimTest(
        "dollar_double_input",
        input="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$trim should reject '$$' as empty variable name in input",
    ),
    TrimTest(
        "dollar_double_chars",
        input="hello",
        chars="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$trim should reject '$$' as empty variable name in chars",
    ),
]

TRIM_INVALID_ARGS_ALL_TESTS = TRIM_SYNTAX_ERROR_TESTS + TRIM_DOLLAR_SIGN_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(TRIM_INVALID_ARGS_ALL_TESTS))
def test_trim_invalid_args(collection, test_case: TrimTest):
    """Test $trim invalid arguments."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
