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

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.last.utils.last_common import (  # noqa: E501
    LastTest,
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

# Property [Arity Errors]: $last takes exactly one argument; zero or two or
# more arguments produce an arity error.
LAST_ARITY_ERROR_TESTS: list[LastTest] = [
    LastTest(
        "arity_zero_args",
        value=[],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$last should reject zero arguments",
    ),
    LastTest(
        "arity_two_args",
        value=["a", "b"],
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$last should reject two arguments",
    ),
]

# Property [Literal Unwrapping Type Error]: a single-element literal array is
# unwrapped at parse time, so $last: ["hello"] becomes $last: "hello" and
# produces a type error, not an arity error.
LAST_LITERAL_UNWRAP_ERROR_TESTS: list[LastTest] = [
    LastTest(
        "literal_unwrap_string_type_error",
        value=["hello"],
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last of ['hello'] should unwrap to $last: 'hello' and produce type error",
    ),
]

# Property [Type Strictness]: when the argument resolves to a non-array,
# non-null type, $last produces a type error.
LAST_TYPE_STRICTNESS_TESTS: list[LastTest] = [
    LastTest(
        "type_strict_string",
        value="hello",
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject string argument",
    ),
    LastTest(
        "type_strict_int32",
        value=42,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject int32 argument",
    ),
    LastTest(
        "type_strict_int64",
        value=Int64(42),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject int64 argument",
    ),
    LastTest(
        "type_strict_double",
        value=3.14,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject double argument",
    ),
    LastTest(
        "type_strict_decimal128",
        value=Decimal128("123.456"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject Decimal128 argument",
    ),
    LastTest(
        "type_strict_boolean",
        value=True,
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject boolean argument",
    ),
    LastTest(
        "type_strict_object",
        value={"$literal": {"a": 1}},
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject object argument",
    ),
    LastTest(
        "type_strict_objectid",
        value=ObjectId("507f1f77bcf86cd799439011"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject ObjectId argument",
    ),
    LastTest(
        "type_strict_datetime",
        value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject datetime argument",
    ),
    LastTest(
        "type_strict_timestamp",
        value=Timestamp(1, 1),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject Timestamp argument",
    ),
    LastTest(
        "type_strict_binary",
        value=Binary(b"\x01\x02"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject Binary argument",
    ),
    LastTest(
        "type_strict_regex",
        value=Regex("abc", "i"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject Regex argument",
    ),
    LastTest(
        "type_strict_code",
        value=Code("function() {}"),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject Code argument",
    ),
    LastTest(
        "type_strict_code_with_scope",
        value=Code("function() {}", {"x": 1}),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject CodeWithScope argument",
    ),
    LastTest(
        "type_strict_minkey",
        value=MinKey(),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject MinKey argument",
    ),
    LastTest(
        "type_strict_maxkey",
        value=MaxKey(),
        error_code=ARRAY_ELEM_AT_ARRAY_TYPE_ERROR,
        msg="$last should reject MaxKey argument",
    ),
]

LAST_ERROR_ALL_TESTS = (
    LAST_ARITY_ERROR_TESTS + LAST_LITERAL_UNWRAP_ERROR_TESTS + LAST_TYPE_STRICTNESS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LAST_ERROR_ALL_TESTS))
def test_last_error(collection, test_case: LastTest):
    """Test $last cases."""
    result = execute_expression(collection, {"$last": test_case.value})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
