from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    SPLIT_EMPTY_SEPARATOR_ERROR,
    SPLIT_STRING_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.split_common import (
    SplitTest,
    _expr,
)

# Property [Empty Delimiter Error]: an empty string delimiter produces
# SPLIT_EMPTY_SEPARATOR_ERROR.
SPLIT_EMPTY_DELIM_ERROR_TESTS: list[SplitTest] = [
    SplitTest(
        "empty_delim_literal",
        string="abc",
        delimiter="",
        error_code=SPLIT_EMPTY_SEPARATOR_ERROR,
        msg="$split should reject empty string as delimiter",
    ),
    SplitTest(
        "empty_delim_both_empty",
        string="",
        delimiter="",
        error_code=SPLIT_EMPTY_SEPARATOR_ERROR,
        msg="$split should reject empty delimiter even when string is also empty",
    ),
    # Type error in first argument takes precedence over empty delimiter error.
    SplitTest(
        "empty_delim_type_error_precedence",
        string=42,
        delimiter="",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should report string type error before empty delimiter error",
    ),
]


# Property [Syntax Validation]: a bare "$" is rejected as an invalid field path,
# "$$" is rejected as an empty variable name, and "$$NOW" resolves to a datetime which fails
# the type check.
SPLIT_SYNTAX_TESTS: list[SplitTest] = [
    SplitTest(
        "syntax_bare_dollar",
        string="$",
        delimiter="-",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$split should reject bare '$' as invalid field path",
    ),
    SplitTest(
        "syntax_double_dollar_string",
        string="$$",
        delimiter="-",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$split should reject '$$' as empty variable name in string position",
    ),
    SplitTest(
        "syntax_double_dollar_delimiter",
        string="hello",
        delimiter="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$split should reject '$$' as empty variable name in delimiter position",
    ),
    SplitTest(
        "syntax_now_resolves_to_date",
        string="$$NOW",
        delimiter="-",
        error_code=SPLIT_STRING_TYPE_ERROR,
        msg="$split should reject $$NOW which resolves to datetime, not string",
    ),
]

# Property [Arity Error]: providing fewer or more than two arguments produces
# EXPRESSION_TYPE_MISMATCH_ERROR. Raw expressions are needed since the
# dataclass always builds two-arg expressions.
SPLIT_ARITY_ERROR_TESTS: list[SplitTest] = [
    SplitTest(
        "arity_zero",
        expr={"$split": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject zero arguments",
    ),
    SplitTest(
        "arity_one",
        expr={"$split": ["hello"]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject one argument",
    ),
    SplitTest(
        "arity_three",
        expr={"$split": ["hello", "-", "extra"]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject three arguments",
    ),
    # Non-array argument shapes are treated as 1 argument.
    SplitTest(
        "arity_string",
        expr={"$split": "hello"},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare string as non-array argument",
    ),
    SplitTest(
        "arity_int",
        expr={"$split": 42},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare int as non-array argument",
    ),
    SplitTest(
        "arity_float",
        expr={"$split": 3.14},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare float as non-array argument",
    ),
    SplitTest(
        "arity_long",
        expr={"$split": Int64(1)},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare Int64 as non-array argument",
    ),
    SplitTest(
        "arity_decimal",
        expr={"$split": Decimal128("1")},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare Decimal128 as non-array argument",
    ),
    SplitTest(
        "arity_bool",
        expr={"$split": True},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare boolean as non-array argument",
    ),
    SplitTest(
        "arity_null",
        expr={"$split": None},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare null as non-array argument",
    ),
    SplitTest(
        "arity_object",
        expr={"$split": {"a": 1}},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare object as non-array argument",
    ),
    SplitTest(
        "arity_binary",
        expr={"$split": Binary(b"data")},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare binary as non-array argument",
    ),
    SplitTest(
        "arity_date",
        expr={"$split": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare datetime as non-array argument",
    ),
    SplitTest(
        "arity_objectid",
        expr={"$split": ObjectId()},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare ObjectId as non-array argument",
    ),
    SplitTest(
        "arity_regex",
        expr={"$split": Regex("pattern")},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare regex as non-array argument",
    ),
    SplitTest(
        "arity_timestamp",
        expr={"$split": Timestamp(1, 1)},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare Timestamp as non-array argument",
    ),
    SplitTest(
        "arity_minkey",
        expr={"$split": MinKey()},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare MinKey as non-array argument",
    ),
    SplitTest(
        "arity_maxkey",
        expr={"$split": MaxKey()},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare MaxKey as non-array argument",
    ),
    SplitTest(
        "arity_code",
        expr={"$split": Code("function() {}")},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare Code as non-array argument",
    ),
    SplitTest(
        "arity_code_scope",
        expr={"$split": Code("function() {}", {"x": 1})},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$split should reject bare Code with scope as non-array argument",
    ),
]

SPLIT_INVALID_ARGS_TESTS = (
    SPLIT_EMPTY_DELIM_ERROR_TESTS + SPLIT_SYNTAX_TESTS + SPLIT_ARITY_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SPLIT_INVALID_ARGS_TESTS))
def test_split_invalid_args_cases(collection, test_case: SplitTest):
    """Test $split empty delimiter, syntax validation, and arity error cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
