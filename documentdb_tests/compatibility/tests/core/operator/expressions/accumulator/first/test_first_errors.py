from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.first.utils.first_common import (  # noqa: E501
    FirstTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity Errors]: $first takes exactly one argument; zero or two or
# more arguments produce an arity error.
FIRST_ARITY_ERROR_TESTS: list[FirstTest] = [
    FirstTest(
        "arity_zero_args",
        value=[],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$first should reject zero arguments",
    ),
    FirstTest(
        "arity_two_args",
        value=["a", "b"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$first should reject two arguments",
    ),
]

# Property [Literal Unwrapping Type Error]: a single-element literal array is
# unwrapped at parse time, so $first: ["hello"] becomes $first: "hello" and
# produces a type error, not an arity error.
FIRST_LITERAL_UNWRAP_ERROR_TESTS: list[FirstTest] = [
    FirstTest(
        "literal_unwrap_string_type_error",
        value=["hello"],
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first of ['hello'] should unwrap to $first: 'hello' and produce type error",
    ),
]

# Property [Type Strictness]: when the argument resolves to a non-array,
# non-null type, $first produces a type error.
FIRST_TYPE_STRICTNESS_TESTS: list[FirstTest] = [
    FirstTest(
        "type_strict_string",
        value="hello",
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject string argument",
    ),
    FirstTest(
        "type_strict_int32",
        value=42,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject int32 argument",
    ),
    FirstTest(
        "type_strict_int64",
        value=Int64(42),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject int64 argument",
    ),
    FirstTest(
        "type_strict_double",
        value=3.14,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject double argument",
    ),
    FirstTest(
        "type_strict_decimal128",
        value=Decimal128("123.456"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject Decimal128 argument",
    ),
    FirstTest(
        "type_strict_boolean",
        value=True,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject boolean argument",
    ),
    FirstTest(
        "type_strict_object",
        value={"$literal": {"a": 1}},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject object argument",
    ),
    FirstTest(
        "type_strict_objectid",
        value=ObjectId("507f1f77bcf86cd799439011"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject ObjectId argument",
    ),
    FirstTest(
        "type_strict_datetime",
        value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject datetime argument",
    ),
    FirstTest(
        "type_strict_timestamp",
        value=Timestamp(1, 1),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject Timestamp argument",
    ),
    FirstTest(
        "type_strict_binary",
        value=Binary(b"\x01\x02"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject Binary argument",
    ),
    FirstTest(
        "type_strict_regex",
        value=Regex("abc", "i"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject Regex argument",
    ),
    FirstTest(
        "type_strict_code",
        value=Code("function() {}"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject Code argument",
    ),
    FirstTest(
        "type_strict_code_with_scope",
        value=Code("function() {}", {"x": 1}),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject CodeWithScope argument",
    ),
    FirstTest(
        "type_strict_minkey",
        value=MinKey(),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject MinKey argument",
    ),
    FirstTest(
        "type_strict_maxkey",
        value=MaxKey(),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$first should reject MaxKey argument",
    ),
]

FIRST_ERROR_ALL_TESTS = (
    FIRST_ARITY_ERROR_TESTS + FIRST_LITERAL_UNWRAP_ERROR_TESTS + FIRST_TYPE_STRICTNESS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(FIRST_ERROR_ALL_TESTS))
def test_first_error(collection, test_case: FirstTest):
    """Test $first cases."""
    result = execute_expression(collection, {"$first": test_case.value})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
