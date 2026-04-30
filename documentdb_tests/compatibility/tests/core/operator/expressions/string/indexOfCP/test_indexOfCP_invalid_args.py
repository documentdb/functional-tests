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
    INDEXOFCP_STRING_TYPE_ERROR,
    INDEXOFCP_SUBSTRING_TYPE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

from .utils.indexOfCP_common import (
    IndexOfCPTest,
)

# Property [Arity]: fewer than 2 or more than 4 arguments produces an error.
INDEXOFCP_ARITY_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "arity_zero",
        args=[],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject zero arguments",
    ),
    IndexOfCPTest(
        "arity_one",
        args=["hello"],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject one argument",
    ),
    IndexOfCPTest(
        "arity_five",
        args=["hello", "h", 0, 5, 1],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject five arguments",
    ),
]


# Property [Syntax]: the argument must be an array; non-array values produce an error.
INDEXOFCP_SYNTAX_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "syntax_string",
        args="hello",  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject string as argument",
    ),
    IndexOfCPTest(
        "syntax_int",
        args=42,  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject int as argument",
    ),
    IndexOfCPTest(
        "syntax_bool",
        args=True,  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject bool as argument",
    ),
    IndexOfCPTest(
        "syntax_binary",
        args=Binary(b"data"),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject binary as argument",
    ),
    IndexOfCPTest(
        "syntax_date",
        args=datetime(2024, 1, 1, tzinfo=timezone.utc),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject date as argument",
    ),
    IndexOfCPTest(
        "syntax_decimal128",
        args=DECIMAL128_ONE_AND_HALF,  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject decimal128 as argument",
    ),
    IndexOfCPTest(
        "syntax_float",
        args=3.14,  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject float as argument",
    ),
    IndexOfCPTest(
        "syntax_long",
        args=Int64(42),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject long as argument",
    ),
    IndexOfCPTest(
        "syntax_maxkey",
        args=MaxKey(),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject maxkey as argument",
    ),
    IndexOfCPTest(
        "syntax_minkey",
        args=MinKey(),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject minkey as argument",
    ),
    IndexOfCPTest(
        "syntax_object",
        args={"a": 1},  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject object as argument",
    ),
    IndexOfCPTest(
        "syntax_objectid",
        args=ObjectId("507f1f77bcf86cd799439011"),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject objectid as argument",
    ),
    IndexOfCPTest(
        "syntax_regex",
        args=Regex("pattern"),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject regex as argument",
    ),
    IndexOfCPTest(
        "syntax_timestamp",
        args=Timestamp(1, 1),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject timestamp as argument",
    ),
    IndexOfCPTest(
        "syntax_code",
        args=Code("function() {}"),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject javascript code as argument",
    ),
    IndexOfCPTest(
        "syntax_code_scope",
        args=Code("function() {}", {"x": 1}),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject code with scope as argument",
    ),
    IndexOfCPTest(
        "syntax_binary_uuid",
        args=Binary(b"data", 4),  # type: ignore[arg-type]
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$indexOfCP should reject binary UUID as argument",
    ),
]


# Property [Expression Returning Wrong Type]: an expression that resolves to the wrong type at
# runtime is rejected with the appropriate type error for that argument position.
INDEXOFCP_EXPR_TYPE_ERROR_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "expr_type_int_in_string_pos",
        args=[{"$add": [1, 2]}, "sub"],
        error_code=INDEXOFCP_STRING_TYPE_ERROR,
        msg="$indexOfCP should reject expression resolving to int for string arg",
    ),
    IndexOfCPTest(
        "expr_type_int_in_substring_pos",
        args=["hello", {"$add": [1, 2]}],
        error_code=INDEXOFCP_SUBSTRING_TYPE_ERROR,
        msg="$indexOfCP should reject expression resolving to int for substring arg",
    ),
    IndexOfCPTest(
        "expr_type_string_in_start_pos",
        args=["hello", "lo", {"$concat": ["x"]}],
        error_code=INDEXOF_INDEX_TYPE_ERROR,
        msg="$indexOfCP should reject expression resolving to string for start arg",
    ),
]


# Property [Dollar Sign Handling - Error]: a bare "$" is interpreted as a field path and "$$" is
# interpreted as an empty variable name.
INDEXOFCP_DOLLAR_SIGN_ERROR_TESTS: list[IndexOfCPTest] = [
    IndexOfCPTest(
        "dollar_bare_substring",
        args=["a$b", "$"],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$indexOfCP should reject bare '$' as field path in substring",
    ),
    IndexOfCPTest(
        "dollar_double_substring",
        args=["hello", "$$"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$indexOfCP should reject '$$' as empty variable name in substring",
    ),
]

INDEXOFCP_INVALID_ARG_TESTS = (
    INDEXOFCP_ARITY_TESTS
    + INDEXOFCP_SYNTAX_TESTS
    + INDEXOFCP_EXPR_TYPE_ERROR_TESTS
    + INDEXOFCP_DOLLAR_SIGN_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFCP_INVALID_ARG_TESTS))
def test_indexofcp_invalid_args(collection, test_case: IndexOfCPTest):
    """Test $indexOfCP invalid argument handling."""
    result = execute_expression(collection, {"$indexOfCP": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
