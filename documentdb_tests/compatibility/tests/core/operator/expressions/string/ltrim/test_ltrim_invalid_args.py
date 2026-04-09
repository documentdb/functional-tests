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

from .utils.ltrim_common import (
    LtrimTest,
    _expr,
)

# Property [Syntax Validation]: invalid $ltrim object shapes produce errors.
LTRIM_SYNTAX_ERROR_TESTS: list[LtrimTest] = [
    # Non-document arguments produce TRIM_WRONG_TYPE_ERROR.
    LtrimTest(
        "syntax_string",
        expr={"$ltrim": "hello"},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject string as argument",
    ),
    LtrimTest(
        "syntax_array",
        expr={"$ltrim": ["hello"]},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject array as argument",
    ),
    LtrimTest(
        "syntax_null",
        expr={"$ltrim": None},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject null as argument",
    ),
    LtrimTest(
        "syntax_int",
        expr={"$ltrim": 42},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject int as argument",
    ),
    LtrimTest(
        "syntax_bool",
        expr={"$ltrim": True},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject boolean as argument",
    ),
    LtrimTest(
        "syntax_float",
        expr={"$ltrim": 3.14},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject float as argument",
    ),
    LtrimTest(
        "syntax_long",
        expr={"$ltrim": Int64(42)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject Int64 as argument",
    ),
    LtrimTest(
        "syntax_binary",
        expr={"$ltrim": Binary(b"data")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject Binary as argument",
    ),
    LtrimTest(
        "syntax_binary_uuid",
        expr={"$ltrim": Binary(b"data", 4)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject Binary UUID as argument",
    ),
    LtrimTest(
        "syntax_date",
        expr={"$ltrim": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject datetime as argument",
    ),
    LtrimTest(
        "syntax_decimal128",
        expr={"$ltrim": DECIMAL128_ONE_AND_HALF},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject Decimal128 as argument",
    ),
    LtrimTest(
        "syntax_maxkey",
        expr={"$ltrim": MaxKey()},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject MaxKey as argument",
    ),
    LtrimTest(
        "syntax_minkey",
        expr={"$ltrim": MinKey()},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject MinKey as argument",
    ),
    LtrimTest(
        "syntax_objectid",
        expr={"$ltrim": ObjectId("507f1f77bcf86cd799439011")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject ObjectId as argument",
    ),
    LtrimTest(
        "syntax_regex",
        expr={"$ltrim": Regex("pattern")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject Regex as argument",
    ),
    LtrimTest(
        "syntax_timestamp",
        expr={"$ltrim": Timestamp(1, 1)},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject Timestamp as argument",
    ),
    LtrimTest(
        "syntax_code",
        expr={"$ltrim": Code("function() {}")},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject Code as argument",
    ),
    LtrimTest(
        "syntax_code_scope",
        expr={"$ltrim": Code("function() {}", {"x": 1})},
        error_code=TRIM_WRONG_TYPE_ERROR,
        msg="$ltrim should reject Code with scope as argument",
    ),
    # Omitting input entirely.
    LtrimTest(
        "syntax_no_input",
        expr={"$ltrim": {"chars": "a"}},
        error_code=TRIM_MISSING_INPUT_ERROR,
        msg="$ltrim should require the input field",
    ),
    # Empty object.
    LtrimTest(
        "syntax_empty_object",
        expr={"$ltrim": {}},
        error_code=TRIM_MISSING_INPUT_ERROR,
        msg="$ltrim should reject empty object",
    ),
    # Unknown extra field.
    LtrimTest(
        "syntax_unknown_field",
        expr={"$ltrim": {"input": "hello", "unknown": 1}},
        error_code=TRIM_UNKNOWN_FIELD_ERROR,
        msg="$ltrim should reject unknown fields in the argument object",
    ),
    # Case-sensitive field names.
    LtrimTest(
        "syntax_case_sensitive_field",
        expr={"$ltrim": {"Input": "hello"}},
        error_code=TRIM_UNKNOWN_FIELD_ERROR,
        msg="$ltrim should reject case-mismatched field name 'Input'",
    ),
]

# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
LTRIM_DOLLAR_SIGN_ERROR_TESTS: list[LtrimTest] = [
    LtrimTest(
        "dollar_bare_input",
        input="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$ltrim should reject bare '$' as input field path",
    ),
    LtrimTest(
        "dollar_bare_chars",
        input="hello",
        chars="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$ltrim should reject bare '$' as chars field path",
    ),
    LtrimTest(
        "dollar_double_input",
        input="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$ltrim should reject '$$' as empty variable name in input",
    ),
    LtrimTest(
        "dollar_double_chars",
        input="hello",
        chars="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$ltrim should reject '$$' as empty variable name in chars",
    ),
]

LTRIM_INVALID_ARGS_ALL_TESTS = LTRIM_SYNTAX_ERROR_TESTS + LTRIM_DOLLAR_SIGN_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_INVALID_ARGS_ALL_TESTS))
def test_ltrim_invalid_args(collection, test_case: LtrimTest):
    """Test $ltrim syntax validation and dollar sign error cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
