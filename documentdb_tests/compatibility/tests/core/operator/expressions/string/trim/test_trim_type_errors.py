from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TRIM_CHARS_TYPE_ERROR, TRIM_INPUT_TYPE_ERROR
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF, MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.trim.utils.trim_common import (
    TrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Type Strictness - input]: non-string, non-null input produces TRIM_INPUT_TYPE_ERROR.
TRIM_INPUT_TYPE_ERROR_TESTS: list[TrimTest] = [
    TrimTest(
        "type_input_array",
        input=["a"],
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject array as input",
    ),
    TrimTest(
        "type_input_binary",
        input=Binary(b"data"),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject Binary as input",
    ),
    TrimTest(
        "type_input_bool",
        input=True,
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject boolean as input",
    ),
    TrimTest(
        "type_input_date",
        input=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject datetime as input",
    ),
    TrimTest(
        "type_input_decimal128",
        input=DECIMAL128_ONE_AND_HALF,
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject Decimal128 as input",
    ),
    TrimTest(
        "type_input_float",
        input=3.14,
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject float as input",
    ),
    TrimTest(
        "type_input_int",
        input=42,
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject int as input",
    ),
    TrimTest(
        "type_input_long",
        input=Int64(42),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject Int64 as input",
    ),
    TrimTest(
        "type_input_maxkey",
        input=MaxKey(),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject MaxKey as input",
    ),
    TrimTest(
        "type_input_minkey",
        input=MinKey(),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject MinKey as input",
    ),
    TrimTest(
        "type_input_object",
        input={"a": 1},
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject object as input",
    ),
    TrimTest(
        "type_input_objectid",
        input=ObjectId("507f1f77bcf86cd799439011"),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject ObjectId as input",
    ),
    TrimTest(
        "type_input_regex",
        input=Regex("pattern"),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject Regex as input",
    ),
    TrimTest(
        "type_input_timestamp",
        input=Timestamp(1, 1),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject Timestamp as input",
    ),
    TrimTest(
        "type_input_code",
        input=Code("function() {}"),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject Code as input",
    ),
    TrimTest(
        "type_input_code_scope",
        input=Code("function() {}", {"x": 1}),
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject Code with scope as input",
    ),
]

# Property [Type Strictness - chars]: non-string, non-null chars produces TRIM_CHARS_TYPE_ERROR.
TRIM_CHARS_TYPE_ERROR_TESTS: list[TrimTest] = [
    TrimTest(
        "type_chars_array",
        input="hello",
        chars=["a"],
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject array as chars",
    ),
    TrimTest(
        "type_chars_binary",
        input="hello",
        chars=Binary(b"data"),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject Binary as chars",
    ),
    TrimTest(
        "type_chars_bool",
        input="hello",
        chars=True,
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject boolean as chars",
    ),
    TrimTest(
        "type_chars_date",
        input="hello",
        chars=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject datetime as chars",
    ),
    TrimTest(
        "type_chars_decimal128",
        input="hello",
        chars=DECIMAL128_ONE_AND_HALF,
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject Decimal128 as chars",
    ),
    TrimTest(
        "type_chars_float",
        input="hello",
        chars=3.14,
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject float as chars",
    ),
    TrimTest(
        "type_chars_int",
        input="hello",
        chars=42,
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject int as chars",
    ),
    TrimTest(
        "type_chars_long",
        input="hello",
        chars=Int64(42),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject Int64 as chars",
    ),
    TrimTest(
        "type_chars_maxkey",
        input="hello",
        chars=MaxKey(),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject MaxKey as chars",
    ),
    TrimTest(
        "type_chars_minkey",
        input="hello",
        chars=MinKey(),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject MinKey as chars",
    ),
    TrimTest(
        "type_chars_object",
        input="hello",
        chars={"a": 1},
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject object as chars",
    ),
    TrimTest(
        "type_chars_objectid",
        input="hello",
        chars=ObjectId("507f1f77bcf86cd799439011"),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject ObjectId as chars",
    ),
    TrimTest(
        "type_chars_regex",
        input="hello",
        chars=Regex("pattern"),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject Regex as chars",
    ),
    TrimTest(
        "type_chars_timestamp",
        input="hello",
        chars=Timestamp(1, 1),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject Timestamp as chars",
    ),
    TrimTest(
        "type_chars_code",
        input="hello",
        chars=Code("function() {}"),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject Code as chars",
    ),
    TrimTest(
        "type_chars_code_scope",
        input="hello",
        chars=Code("function() {}", {"x": 1}),
        error_code=TRIM_CHARS_TYPE_ERROR,
        msg="$trim should reject Code with scope as chars",
    ),
]

# Property [Type Strictness - precedence]: when both input and chars are non-string, the input
# type error takes precedence.
TRIM_TYPE_PRECEDENCE_TESTS: list[TrimTest] = [
    TrimTest(
        "type_precedence_both_int",
        input=123,
        chars=456,
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should report input type error before chars type error when both are invalid",
    ),
]

# Property [Type Strictness - input with null chars]: non-string input errors even when chars is
# null or missing.
TRIM_INPUT_TYPE_NULL_CHARS_TESTS: list[TrimTest] = [
    TrimTest(
        "type_input_int_chars_null",
        input=123,
        chars=None,
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject non-string input even when chars is null",
    ),
    TrimTest(
        "type_input_int_chars_missing",
        input=123,
        chars=MISSING,
        error_code=TRIM_INPUT_TYPE_ERROR,
        msg="$trim should reject non-string input even when chars is missing",
    ),
]

TRIM_TYPE_ERROR_ALL_TESTS = (
    TRIM_INPUT_TYPE_ERROR_TESTS
    + TRIM_CHARS_TYPE_ERROR_TESTS
    + TRIM_TYPE_PRECEDENCE_TESTS
    + TRIM_INPUT_TYPE_NULL_CHARS_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(TRIM_TYPE_ERROR_ALL_TESTS))
def test_trim_type_errors(collection, test_case: TrimTest):
    """Test $trim type errors."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
