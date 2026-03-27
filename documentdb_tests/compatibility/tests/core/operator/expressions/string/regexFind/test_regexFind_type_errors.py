from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    REGEX_INPUT_TYPE_ERROR,
    REGEX_OPTIONS_TYPE_ERROR,
    REGEX_REGEX_TYPE_ERROR,
)
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexFind.utils.regexFind_common import (
    RegexFindTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Type Strictness - input]: non-string, non-null input produces an error.
REGEXFIND_INPUT_TYPE_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "type_input_array",
        input=["a"],
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject array as input",
    ),
    RegexFindTest(
        "type_input_binary",
        input=Binary(b"data"),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject binary as input",
    ),
    RegexFindTest(
        "type_input_bool",
        input=True,
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject bool as input",
    ),
    RegexFindTest(
        "type_input_date",
        input=datetime(2024, 1, 1, tzinfo=timezone.utc),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject date as input",
    ),
    RegexFindTest(
        "type_input_decimal128",
        input=DECIMAL128_ONE_AND_HALF,
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject decimal128 as input",
    ),
    RegexFindTest(
        "type_input_float",
        input=3.14,
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject float as input",
    ),
    RegexFindTest(
        "type_input_int",
        input=42,
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject int as input",
    ),
    RegexFindTest(
        "type_input_long",
        input=Int64(42),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject long as input",
    ),
    RegexFindTest(
        "type_input_maxkey",
        input=MaxKey(),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject maxkey as input",
    ),
    RegexFindTest(
        "type_input_minkey",
        input=MinKey(),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject minkey as input",
    ),
    RegexFindTest(
        "type_input_object",
        input={"a": 1},
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject object as input",
    ),
    RegexFindTest(
        "type_input_objectid",
        input=ObjectId("507f1f77bcf86cd799439011"),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject objectid as input",
    ),
    RegexFindTest(
        "type_input_regex",
        input=Regex("pattern"),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject regex as input",
    ),
    RegexFindTest(
        "type_input_timestamp",
        input=Timestamp(1, 1),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject timestamp as input",
    ),
    RegexFindTest(
        "type_input_code",
        input=Code("function() {}"),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject javascript code as input",
    ),
    RegexFindTest(
        "type_input_code_scope",
        input=Code("function() {}", {"x": 1}),
        regex="abc",
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should reject code with scope as input",
    ),
]

# Property [Type Strictness - regex]: non-string, non-Regex, non-null regex produces an error.
REGEXFIND_REGEX_TYPE_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "type_regex_array",
        input="hello",
        regex=["a"],
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject array as regex",
    ),
    RegexFindTest(
        "type_regex_binary",
        input="hello",
        regex=Binary(b"data"),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject binary as regex",
    ),
    RegexFindTest(
        "type_regex_bool",
        input="hello",
        regex=True,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject bool as regex",
    ),
    RegexFindTest(
        "type_regex_date",
        input="hello",
        regex=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject date as regex",
    ),
    RegexFindTest(
        "type_regex_decimal128",
        input="hello",
        regex=DECIMAL128_ONE_AND_HALF,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject decimal128 as regex",
    ),
    RegexFindTest(
        "type_regex_float",
        input="hello",
        regex=3.14,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject float as regex",
    ),
    RegexFindTest(
        "type_regex_int",
        input="hello",
        regex=42,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject int as regex",
    ),
    RegexFindTest(
        "type_regex_long",
        input="hello",
        regex=Int64(42),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject long as regex",
    ),
    RegexFindTest(
        "type_regex_maxkey",
        input="hello",
        regex=MaxKey(),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject maxkey as regex",
    ),
    RegexFindTest(
        "type_regex_minkey",
        input="hello",
        regex=MinKey(),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject minkey as regex",
    ),
    RegexFindTest(
        "type_regex_object",
        input="hello",
        regex={"a": 1},
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject object as regex",
    ),
    RegexFindTest(
        "type_regex_objectid",
        input="hello",
        regex=ObjectId("507f1f77bcf86cd799439011"),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject objectid as regex",
    ),
    RegexFindTest(
        "type_regex_timestamp",
        input="hello",
        regex=Timestamp(1, 1),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject timestamp as regex",
    ),
    RegexFindTest(
        "type_regex_code",
        input="hello",
        regex=Code("function() {}"),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject javascript code as regex",
    ),
    RegexFindTest(
        "type_regex_code_scope",
        input="hello",
        regex=Code("function() {}", {"x": 1}),
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should reject code with scope as regex",
    ),
]

# Property [Type Strictness - options]: non-string options (excluding null) produces an error.
REGEXFIND_OPTIONS_TYPE_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "type_options_array",
        input="hello",
        regex="hello",
        options=["a"],
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject array as options",
    ),
    RegexFindTest(
        "type_options_binary",
        input="hello",
        regex="hello",
        options=Binary(b"data"),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject binary as options",
    ),
    RegexFindTest(
        "type_options_bool",
        input="hello",
        regex="hello",
        options=True,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject bool as options",
    ),
    RegexFindTest(
        "type_options_date",
        input="hello",
        regex="hello",
        options=datetime(2024, 1, 1, tzinfo=timezone.utc),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject date as options",
    ),
    RegexFindTest(
        "type_options_decimal128",
        input="hello",
        regex="hello",
        options=DECIMAL128_ONE_AND_HALF,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject decimal128 as options",
    ),
    RegexFindTest(
        "type_options_float",
        input="hello",
        regex="hello",
        options=3.14,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject float as options",
    ),
    RegexFindTest(
        "type_options_int",
        input="hello",
        regex="hello",
        options=42,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject int as options",
    ),
    RegexFindTest(
        "type_options_long",
        input="hello",
        regex="hello",
        options=Int64(42),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject long as options",
    ),
    RegexFindTest(
        "type_options_maxkey",
        input="hello",
        regex="hello",
        options=MaxKey(),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject maxkey as options",
    ),
    RegexFindTest(
        "type_options_minkey",
        input="hello",
        regex="hello",
        options=MinKey(),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject minkey as options",
    ),
    RegexFindTest(
        "type_options_object",
        input="hello",
        regex="hello",
        options={"a": 1},
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject object as options",
    ),
    RegexFindTest(
        "type_options_objectid",
        input="hello",
        regex="hello",
        options=ObjectId("507f1f77bcf86cd799439011"),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject objectid as options",
    ),
    RegexFindTest(
        "type_options_regex",
        input="hello",
        regex="hello",
        options=Regex("pattern"),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject regex as options",
    ),
    RegexFindTest(
        "type_options_timestamp",
        input="hello",
        regex="hello",
        options=Timestamp(1, 1),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject timestamp as options",
    ),
    RegexFindTest(
        "type_options_code",
        input="hello",
        regex="hello",
        options=Code("function() {}"),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject javascript code as options",
    ),
    RegexFindTest(
        "type_options_code_scope",
        input="hello",
        regex="hello",
        options=Code("function() {}", {"x": 1}),
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind should reject code with scope as options",
    ),
]

REGEXFIND_TYPE_ERROR_ALL_TESTS = (
    REGEXFIND_INPUT_TYPE_TESTS + REGEXFIND_REGEX_TYPE_TESTS + REGEXFIND_OPTIONS_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFIND_TYPE_ERROR_ALL_TESTS))
def test_regexfind_cases(collection, test_case: RegexFindTest):
    """Test $regexFind type error cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
