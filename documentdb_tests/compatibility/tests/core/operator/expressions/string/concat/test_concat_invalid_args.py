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
    CONCAT_TYPE_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF, MISSING

from .utils.concat_common import (
    ConcatTest,
)

# Property [Syntax Validation]: non-array argument of invalid type produces CONCAT_TYPE_ERROR.
CONCAT_SYNTAX_ERROR_TESTS: list[ConcatTest] = [
    ConcatTest(
        "syntax_binary",
        args=Binary(b"data"),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare binary as non-array argument",
    ),
    ConcatTest(
        "syntax_bool",
        args=True,  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare boolean as non-array argument",
    ),
    ConcatTest(
        "syntax_date",
        args=datetime(2024, 1, 1, tzinfo=timezone.utc),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare datetime as non-array argument",
    ),
    ConcatTest(
        "syntax_decimal128",
        args=DECIMAL128_ONE_AND_HALF,  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare Decimal128 as non-array argument",
    ),
    ConcatTest(
        "syntax_float",
        args=3.14,  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare float as non-array argument",
    ),
    ConcatTest(
        "syntax_int",
        args=42,  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare int as non-array argument",
    ),
    ConcatTest(
        "syntax_long",
        args=Int64(42),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare Int64 as non-array argument",
    ),
    ConcatTest(
        "syntax_maxkey",
        args=MaxKey(),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare MaxKey as non-array argument",
    ),
    ConcatTest(
        "syntax_minkey",
        args=MinKey(),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare MinKey as non-array argument",
    ),
    ConcatTest(
        "syntax_object",
        args={"a": 1},  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare object as non-array argument",
    ),
    ConcatTest(
        "syntax_objectid",
        args=ObjectId("507f1f77bcf86cd799439011"),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare ObjectId as non-array argument",
    ),
    ConcatTest(
        "syntax_regex",
        args=Regex("pattern"),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare regex as non-array argument",
    ),
    ConcatTest(
        "syntax_timestamp",
        args=Timestamp(1, 1),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare Timestamp as non-array argument",
    ),
    ConcatTest(
        "syntax_code",
        args=Code("function() {}"),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare Code as non-array argument",
    ),
    ConcatTest(
        "syntax_code_scope",
        args=Code("function() {}", {"x": 1}),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare Code with scope as non-array argument",
    ),
    ConcatTest(
        "syntax_binary_uuid",
        args=Binary(b"data", 4),  # type: ignore[arg-type]
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject bare binary UUID as non-array argument",
    ),
]

# Property [Expression Returning Wrong Type]: an expression that resolves to a non-string, non-null
# type at runtime is rejected with CONCAT_TYPE_ERROR.
CONCAT_EXPR_TYPE_ERROR_TESTS: list[ConcatTest] = [
    ConcatTest(
        "expr_type_int_solo",
        args=[{"$add": [1, 2]}],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject expression resolving to int",
    ),
    ConcatTest(
        "expr_type_int_after_string",
        args=["hello", {"$add": [1, 2]}],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject expression resolving to int after string",
    ),
    ConcatTest(
        "expr_type_int_before_string",
        args=[{"$add": [1, 2]}, "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should reject expression resolving to int before string",
    ),
]

# Property [Error Precedence - Type Error Wins]: when a type-invalid argument appears before null or
# missing in left-to-right order, the type error is reported.
CONCAT_ERROR_PREC_TYPE_WINS_TESTS: list[ConcatTest] = [
    ConcatTest(
        "error_prec_int_before_null",
        args=[42, None],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should report type error when int precedes null",
    ),
    ConcatTest(
        "error_prec_int_null_str",
        args=[42, None, "hello"],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should report type error when int precedes null and string",
    ),
    ConcatTest(
        "error_prec_int_before_missing",
        args=[42, MISSING],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should report type error when int precedes missing",
    ),
    ConcatTest(
        "error_prec_leftmost_reported",
        args=[42, True],
        error_code=CONCAT_TYPE_ERROR,
        msg="$concat should report type error for leftmost invalid argument",
    ),
]

# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
CONCAT_DOLLAR_SIGN_ERROR_TESTS: list[ConcatTest] = [
    ConcatTest(
        "dollar_bare",
        args=["$"],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$concat should reject bare '$' as invalid field path",
    ),
    ConcatTest(
        "dollar_double",
        args=["$$"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$concat should reject '$$' as empty variable name",
    ),
]

CONCAT_INVALID_ARGS_TESTS = (
    CONCAT_SYNTAX_ERROR_TESTS
    + CONCAT_EXPR_TYPE_ERROR_TESTS
    + CONCAT_ERROR_PREC_TYPE_WINS_TESTS
    + CONCAT_DOLLAR_SIGN_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_INVALID_ARGS_TESTS))
def test_concat_invalid_args_cases(collection, test_case: ConcatTest):
    """Test $concat invalid argument cases."""
    result = execute_expression(collection, {"$concat": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
