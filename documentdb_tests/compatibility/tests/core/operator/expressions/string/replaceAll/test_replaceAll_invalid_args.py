from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    REPLACE_MISSING_FIND_ERROR,
    REPLACE_MISSING_INPUT_ERROR,
    REPLACE_MISSING_REPLACEMENT_ERROR,
    REPLACE_NON_OBJECT_ERROR,
    REPLACE_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

from .utils.replaceAll_common import (
    ReplaceAllTest,
    _expr,
)

# Property [Bare Dollar Sign]: a bare "$" string in any parameter position is interpreted as a
# field path, producing INVALID_DOLLAR_FIELD_PATH.
REPLACEALL_BARE_DOLLAR_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "bare_dollar_input",
        input="$",
        find="a",
        replacement="b",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$replaceAll should reject bare '$' in input",
    ),
    ReplaceAllTest(
        "bare_dollar_find",
        input="hello",
        find="$",
        replacement="b",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$replaceAll should reject bare '$' in find",
    ),
    ReplaceAllTest(
        "bare_dollar_replacement",
        input="hello",
        find="a",
        replacement="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$replaceAll should reject bare '$' in replacement",
    ),
]


# Property [Double Dollar Sign]: a "$$" string in any parameter position produces
# FAILED_TO_PARSE_ERROR.
REPLACEALL_DOUBLE_DOLLAR_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "double_dollar_input",
        input="$$",
        find="a",
        replacement="b",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$replaceAll should reject '$$' in input",
    ),
    ReplaceAllTest(
        "double_dollar_find",
        input="hello",
        find="$$",
        replacement="b",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$replaceAll should reject '$$' in find",
    ),
    ReplaceAllTest(
        "double_dollar_replacement",
        input="hello",
        find="a",
        replacement="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$replaceAll should reject '$$' in replacement",
    ),
]


# Property [Syntax Validation - Non-Object]: a non-object argument to $replaceAll produces
# REPLACE_NON_OBJECT_ERROR.
REPLACEALL_NON_OBJECT_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "syntax_string",
        expr={"$replaceAll": "hello"},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject string",
    ),
    ReplaceAllTest(
        "syntax_int",
        expr={"$replaceAll": 42},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject int",
    ),
    ReplaceAllTest(
        "syntax_float",
        expr={"$replaceAll": 3.14},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject float",
    ),
    ReplaceAllTest(
        "syntax_long",
        expr={"$replaceAll": Int64(42)},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject long",
    ),
    ReplaceAllTest(
        "syntax_decimal128",
        expr={"$replaceAll": DECIMAL128_ONE_AND_HALF},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject decimal128",
    ),
    ReplaceAllTest(
        "syntax_null",
        expr={"$replaceAll": None},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject null",
    ),
    ReplaceAllTest(
        "syntax_bool",
        expr={"$replaceAll": True},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject bool",
    ),
    ReplaceAllTest(
        "syntax_array",
        expr={"$replaceAll": ["a", "b", "c"]},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject array",
    ),
    ReplaceAllTest(
        "syntax_binary",
        expr={"$replaceAll": Binary(b"data")},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject binary",
    ),
    ReplaceAllTest(
        "syntax_date",
        expr={"$replaceAll": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject date",
    ),
    ReplaceAllTest(
        "syntax_objectid",
        expr={"$replaceAll": ObjectId()},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject objectid",
    ),
    ReplaceAllTest(
        "syntax_regex",
        expr={"$replaceAll": Regex("pattern")},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject regex",
    ),
    ReplaceAllTest(
        "syntax_timestamp",
        expr={"$replaceAll": Timestamp(1, 1)},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject timestamp",
    ),
    ReplaceAllTest(
        "syntax_minkey",
        expr={"$replaceAll": MinKey()},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject minkey",
    ),
    ReplaceAllTest(
        "syntax_maxkey",
        expr={"$replaceAll": MaxKey()},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject maxkey",
    ),
    ReplaceAllTest(
        "syntax_code",
        expr={"$replaceAll": Code("function() {}")},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject code",
    ),
    ReplaceAllTest(
        "syntax_code_scope",
        expr={"$replaceAll": Code("function() {}", {"x": 1})},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceAll should reject code scope",
    ),
]


# Property [Syntax Validation - Missing and Unknown Fields]: omitting required fields or including
# unknown fields produces a specific error, with precedence non-object > unknown field > missing
# input > missing find > missing replacement > type errors.
REPLACEALL_FIELD_VALIDATION_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "syntax_missing_input",
        expr={"$replaceAll": {"find": "a", "replacement": "b"}},
        error_code=REPLACE_MISSING_INPUT_ERROR,
        msg="$replaceAll should reject missing input",
    ),
    ReplaceAllTest(
        "syntax_missing_find",
        expr={"$replaceAll": {"input": "hello", "replacement": "b"}},
        error_code=REPLACE_MISSING_FIND_ERROR,
        msg="$replaceAll should reject missing find",
    ),
    ReplaceAllTest(
        "syntax_missing_replacement",
        expr={"$replaceAll": {"input": "hello", "find": "a"}},
        error_code=REPLACE_MISSING_REPLACEMENT_ERROR,
        msg="$replaceAll should reject missing replacement",
    ),
    ReplaceAllTest(
        "syntax_unknown_field",
        expr={"$replaceAll": {"input": "hello", "find": "a", "replacement": "b", "extra": 1}},
        error_code=REPLACE_UNKNOWN_FIELD_ERROR,
        msg="$replaceAll should reject unknown field",
    ),
    # Missing input takes precedence over missing find.
    ReplaceAllTest(
        "syntax_missing_input_and_find",
        expr={"$replaceAll": {"replacement": "b"}},
        error_code=REPLACE_MISSING_INPUT_ERROR,
        msg="$replaceAll should reject missing input and find",
    ),
    # Missing input takes precedence over missing replacement.
    ReplaceAllTest(
        "syntax_missing_input_and_replacement",
        expr={"$replaceAll": {"find": "a"}},
        error_code=REPLACE_MISSING_INPUT_ERROR,
        msg="$replaceAll should reject missing input and replacement",
    ),
    # Missing find takes precedence over missing replacement.
    ReplaceAllTest(
        "syntax_missing_find_and_replacement",
        expr={"$replaceAll": {"input": "hello"}},
        error_code=REPLACE_MISSING_FIND_ERROR,
        msg="$replaceAll should reject missing find and replacement",
    ),
    # Missing all required fields: input validated first.
    ReplaceAllTest(
        "syntax_missing_all",
        expr={"$replaceAll": {}},
        error_code=REPLACE_MISSING_INPUT_ERROR,
        msg="$replaceAll should reject missing all",
    ),
    # Unknown field takes precedence over missing fields.
    ReplaceAllTest(
        "syntax_unknown_precedes_missing",
        expr={"$replaceAll": {"extra": 1}},
        error_code=REPLACE_UNKNOWN_FIELD_ERROR,
        msg="$replaceAll should reject unknown precedes missing",
    ),
]


REPLACEALL_INVALID_ARGS_ALL_TESTS = (
    REPLACEALL_BARE_DOLLAR_TESTS
    + REPLACEALL_DOUBLE_DOLLAR_TESTS
    + REPLACEALL_NON_OBJECT_TESTS
    + REPLACEALL_FIELD_VALIDATION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_INVALID_ARGS_ALL_TESTS))
def test_replaceall_invalid_args_cases(collection, test_case: ReplaceAllTest):
    """Test $replaceAll invalid argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
