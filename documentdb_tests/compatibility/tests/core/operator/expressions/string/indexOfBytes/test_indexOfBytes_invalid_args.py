from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    FAILED_TO_PARSE_ERROR,
    INDEXOF_INDEX_TYPE_ERROR,
    INDEXOFBYTES_STRING_TYPE_ERROR,
    INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

from .utils.indexOfBytes_common import (
    IndexOfBytesTest,
)

# Property [Arity]: fewer than 2 or more than 4 arguments produces an error.
INDEXOFBYTES_ARITY_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "arity_zero",
        args=[],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject zero arguments",
    ),
    IndexOfBytesTest(
        "arity_one",
        args=["hello"],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject one argument",
    ),
    IndexOfBytesTest(
        "arity_five",
        args=["hello", "h", 0, 5, 1],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject five arguments",
    ),
]

# Property [Syntax]: the argument must be an array; non-array values produce an error.
INDEXOFBYTES_SYNTAX_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "syntax_string",
        args="hello",  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject string as argument",
    ),
    IndexOfBytesTest(
        "syntax_int",
        args=42,  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject int as argument",
    ),
    IndexOfBytesTest(
        "syntax_bool",
        args=True,  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject bool as argument",
    ),
    IndexOfBytesTest(
        "syntax_binary",
        args=Binary(b"data"),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject binary as argument",
    ),
    IndexOfBytesTest(
        "syntax_date",
        args=datetime(2024, 1, 1, tzinfo=timezone.utc),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject date as argument",
    ),
    IndexOfBytesTest(
        "syntax_decimal128",
        args=DECIMAL128_ONE_AND_HALF,  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject decimal128 as argument",
    ),
    IndexOfBytesTest(
        "syntax_float",
        args=3.14,  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject float as argument",
    ),
    IndexOfBytesTest(
        "syntax_long",
        args=Int64(42),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject long as argument",
    ),
    IndexOfBytesTest(
        "syntax_maxkey",
        args=MaxKey(),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject maxkey as argument",
    ),
    IndexOfBytesTest(
        "syntax_minkey",
        args=MinKey(),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject minkey as argument",
    ),
    IndexOfBytesTest(
        "syntax_object",
        args={"a": 1},  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject object as argument",
    ),
    IndexOfBytesTest(
        "syntax_objectid",
        args=ObjectId("507f1f77bcf86cd799439011"),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject objectid as argument",
    ),
    IndexOfBytesTest(
        "syntax_regex",
        args=Regex("pattern"),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject regex as argument",
    ),
    IndexOfBytesTest(
        "syntax_timestamp",
        args=Timestamp(1, 1),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject timestamp as argument",
    ),
    IndexOfBytesTest(
        "syntax_code",
        args=Code("function() {}"),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject javascript code as argument",
    ),
    IndexOfBytesTest(
        "syntax_code_scope",
        args=Code("function() {}", {"x": 1}),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject code with scope as argument",
    ),
    IndexOfBytesTest(
        "syntax_binary_uuid",
        args=Binary(b"data", 4),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfBytes should reject binary UUID as argument",
    ),
]

# Property [Expression Returning Wrong Type]: an expression that resolves to the wrong type at
# runtime is rejected with the same error as a literal of that type.
INDEXOFBYTES_EXPR_TYPE_ERROR_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "expr_type_int_string_pos",
        args=[{"$add": [1, 2]}, "lo"],
        error_code=INDEXOFBYTES_STRING_TYPE_ERROR,
        msg="$indexOfBytes should reject expression resolving to int for string arg",
    ),
    IndexOfBytesTest(
        "expr_type_int_substring_pos",
        args=["hello", {"$add": [1, 2]}],
        error_code=INDEXOFBYTES_SUBSTRING_TYPE_ERROR,
        msg="$indexOfBytes should reject expression resolving to int for substring arg",
    ),
    IndexOfBytesTest(
        "expr_type_string_start_pos",
        args=["hello", "lo", {"$concat": ["x"]}],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfBytes should reject expression resolving to string for start arg",
    ),
]

# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
INDEXOFBYTES_DOLLAR_SIGN_ERROR_TESTS: list[IndexOfBytesTest] = [
    IndexOfBytesTest(
        "dollar_bare_error",
        args=["hello$world", "$"],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$indexOfBytes should reject bare '$' as field path in substring",
    ),
    IndexOfBytesTest(
        "dollar_double_error",
        args=["hello", "$$"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$indexOfBytes should reject '$$' as empty variable name in substring",
    ),
]


INDEXOFBYTES_INVALID_ARGS_TESTS = (
    INDEXOFBYTES_ARITY_TESTS
    + INDEXOFBYTES_SYNTAX_TESTS
    + INDEXOFBYTES_EXPR_TYPE_ERROR_TESTS
    + INDEXOFBYTES_DOLLAR_SIGN_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFBYTES_INVALID_ARGS_TESTS))
def test_indexofbytes_cases(collection, test_case: IndexOfBytesTest):
    """Test $indexOfBytes cases."""
    result = execute_expression(collection, {"$indexOfBytes": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
