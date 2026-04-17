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
    REPLACE_FIND_TYPE_ERROR,
    REPLACE_INPUT_TYPE_ERROR,
    REPLACE_MISSING_FIND_ERROR,
    REPLACE_MISSING_INPUT_ERROR,
    REPLACE_MISSING_REPLACEMENT_ERROR,
    REPLACE_NON_OBJECT_ERROR,
    REPLACE_REPLACEMENT_TYPE_ERROR,
    REPLACE_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF, MISSING

from .utils.replaceOne_common import (
    ReplaceOneTest,
    _expr,
)

# Property [Type Error Precedence]: type errors take precedence over null
# propagation. When multiple arguments have type errors, input is validated
# first, then find, then replacement.
REPLACEONE_TYPE_PRECEDENCE_TESTS: list[ReplaceOneTest] = [
    # Type error on find takes precedence over null input.
    ReplaceOneTest(
        "precedence_null_input_type_find",
        input=None,
        find=123,
        replacement="b",
        error_code=REPLACE_FIND_TYPE_ERROR,
        msg="$replaceOne precedence: null input type find",
    ),
    # Type error on replacement takes precedence over null input.
    ReplaceOneTest(
        "precedence_null_input_type_replacement",
        input=None,
        find="a",
        replacement=123,
        error_code=REPLACE_REPLACEMENT_TYPE_ERROR,
        msg="$replaceOne precedence: null input type replacement",
    ),
    # Type error on replacement takes precedence over null find.
    ReplaceOneTest(
        "precedence_null_find_type_replacement",
        input="hello",
        find=None,
        replacement=123,
        error_code=REPLACE_REPLACEMENT_TYPE_ERROR,
        msg="$replaceOne precedence: null find type replacement",
    ),
    # Input type error takes precedence over find type error.
    ReplaceOneTest(
        "precedence_input_before_find",
        input=123,
        find=456,
        replacement="b",
        error_code=REPLACE_INPUT_TYPE_ERROR,
        msg="$replaceOne precedence: input before find",
    ),
    # Input type error takes precedence over replacement type error.
    ReplaceOneTest(
        "precedence_input_before_replacement",
        input=123,
        find="a",
        replacement=456,
        error_code=REPLACE_INPUT_TYPE_ERROR,
        msg="$replaceOne precedence: input before replacement",
    ),
    # Find type error takes precedence over replacement type error.
    ReplaceOneTest(
        "precedence_find_before_replacement",
        input="hello",
        find=123,
        replacement=456,
        error_code=REPLACE_FIND_TYPE_ERROR,
        msg="$replaceOne precedence: find before replacement",
    ),
    # All three have type errors: input wins.
    ReplaceOneTest(
        "precedence_all_type_errors",
        input=123,
        find=456,
        replacement=789,
        error_code=REPLACE_INPUT_TYPE_ERROR,
        msg="$replaceOne precedence: all type errors",
    ),
    # Missing input does not shield type error on find.
    ReplaceOneTest(
        "precedence_missing_input_type_find",
        input=MISSING,
        find=123,
        replacement="b",
        error_code=REPLACE_FIND_TYPE_ERROR,
        msg="$replaceOne precedence: missing input type find",
    ),
    # Missing input does not shield type error on replacement.
    ReplaceOneTest(
        "precedence_missing_input_type_replacement",
        input=MISSING,
        find="a",
        replacement=123,
        error_code=REPLACE_REPLACEMENT_TYPE_ERROR,
        msg="$replaceOne precedence: missing input type replacement",
    ),
    # Missing find does not shield type error on replacement.
    ReplaceOneTest(
        "precedence_missing_find_type_replacement",
        input="hello",
        find=MISSING,
        replacement=123,
        error_code=REPLACE_REPLACEMENT_TYPE_ERROR,
        msg="$replaceOne precedence: missing find type replacement",
    ),
]

# Property [Bare Dollar Sign]: a bare "$" string in any parameter position is
# interpreted as a field path, producing INVALID_DOLLAR_FIELD_PATH.
REPLACEONE_BARE_DOLLAR_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "bare_dollar_input",
        input="$",
        find="a",
        replacement="b",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$replaceOne should reject bare '$' in input",
    ),
    ReplaceOneTest(
        "bare_dollar_find",
        input="hello",
        find="$",
        replacement="b",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$replaceOne should reject bare '$' in find",
    ),
    ReplaceOneTest(
        "bare_dollar_replacement",
        input="hello",
        find="a",
        replacement="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$replaceOne should reject bare '$' in replacement",
    ),
]

# Property [Double Dollar Sign]: a "$$" string in any parameter position is interpreted as a
# variable reference with an empty name, producing FAILED_TO_PARSE_ERROR.
REPLACEONE_DOUBLE_DOLLAR_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "double_dollar_input",
        input="$$",
        find="a",
        replacement="b",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$replaceOne should reject '$$' in input",
    ),
    ReplaceOneTest(
        "double_dollar_find",
        input="hello",
        find="$$",
        replacement="b",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$replaceOne should reject '$$' in find",
    ),
    ReplaceOneTest(
        "double_dollar_replacement",
        input="hello",
        find="a",
        replacement="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$replaceOne should reject '$$' in replacement",
    ),
]


# Property [Syntax Validation - Non-Object]: a non-object argument to
# $replaceOne produces REPLACE_NON_OBJECT_ERROR.
REPLACEONE_NON_OBJECT_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "syntax_string",
        expr={"$replaceOne": "hello"},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject string",
    ),
    ReplaceOneTest(
        "syntax_int",
        expr={"$replaceOne": 42},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject int",
    ),
    ReplaceOneTest(
        "syntax_float",
        expr={"$replaceOne": 3.14},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject float",
    ),
    ReplaceOneTest(
        "syntax_long",
        expr={"$replaceOne": Int64(42)},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject long",
    ),
    ReplaceOneTest(
        "syntax_decimal128",
        expr={"$replaceOne": DECIMAL128_ONE_AND_HALF},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject decimal128",
    ),
    ReplaceOneTest(
        "syntax_null",
        expr={"$replaceOne": None},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject null",
    ),
    ReplaceOneTest(
        "syntax_bool",
        expr={"$replaceOne": True},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject bool",
    ),
    ReplaceOneTest(
        "syntax_array",
        expr={"$replaceOne": ["a", "b", "c"]},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject array",
    ),
    ReplaceOneTest(
        "syntax_binary",
        expr={"$replaceOne": Binary(b"data")},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject binary",
    ),
    ReplaceOneTest(
        "syntax_date",
        expr={"$replaceOne": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject date",
    ),
    ReplaceOneTest(
        "syntax_objectid",
        expr={"$replaceOne": ObjectId()},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject objectid",
    ),
    ReplaceOneTest(
        "syntax_regex",
        expr={"$replaceOne": Regex("pattern")},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject regex",
    ),
    ReplaceOneTest(
        "syntax_timestamp",
        expr={"$replaceOne": Timestamp(1, 1)},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject timestamp",
    ),
    ReplaceOneTest(
        "syntax_minkey",
        expr={"$replaceOne": MinKey()},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject minkey",
    ),
    ReplaceOneTest(
        "syntax_maxkey",
        expr={"$replaceOne": MaxKey()},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject maxkey",
    ),
    ReplaceOneTest(
        "syntax_code",
        expr={"$replaceOne": Code("function() {}")},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject code",
    ),
    ReplaceOneTest(
        "syntax_code_scope",
        expr={"$replaceOne": Code("function() {}", {"x": 1})},
        error_code=REPLACE_NON_OBJECT_ERROR,
        msg="$replaceOne should reject code scope",
    ),
]

# Property [Syntax Validation - Missing and Unknown Fields]: omitting required
# fields or including unknown fields produces a specific error, with precedence
# non-object > unknown field > missing input > missing find > missing
# replacement > type errors.
REPLACEONE_FIELD_VALIDATION_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "syntax_missing_input",
        expr={"$replaceOne": {"find": "a", "replacement": "b"}},
        error_code=REPLACE_MISSING_INPUT_ERROR,
        msg="$replaceOne should reject missing input",
    ),
    ReplaceOneTest(
        "syntax_missing_find",
        expr={"$replaceOne": {"input": "hello", "replacement": "b"}},
        error_code=REPLACE_MISSING_FIND_ERROR,
        msg="$replaceOne should reject missing find",
    ),
    ReplaceOneTest(
        "syntax_missing_replacement",
        expr={"$replaceOne": {"input": "hello", "find": "a"}},
        error_code=REPLACE_MISSING_REPLACEMENT_ERROR,
        msg="$replaceOne should reject missing replacement",
    ),
    # Empty object produces missing input error.
    ReplaceOneTest(
        "syntax_empty_object",
        expr={"$replaceOne": {}},
        error_code=REPLACE_MISSING_INPUT_ERROR,
        msg="$replaceOne should reject empty object",
    ),
    # Unknown field.
    ReplaceOneTest(
        "syntax_unknown_field",
        expr={"$replaceOne": {"input": "hello", "find": "a", "replacement": "b", "extra": 1}},
        error_code=REPLACE_UNKNOWN_FIELD_ERROR,
        msg="$replaceOne should reject unknown field",
    ),
    # Case-sensitive field names are treated as unknown.
    ReplaceOneTest(
        "syntax_case_sensitive_input",
        expr={"$replaceOne": {"Input": "hello", "find": "a", "replacement": "b"}},
        error_code=REPLACE_UNKNOWN_FIELD_ERROR,
        msg="$replaceOne should reject case sensitive input",
    ),
    ReplaceOneTest(
        "syntax_case_sensitive_find",
        expr={"$replaceOne": {"input": "hello", "Find": "a", "replacement": "b"}},
        error_code=REPLACE_UNKNOWN_FIELD_ERROR,
        msg="$replaceOne should reject case sensitive find",
    ),
    ReplaceOneTest(
        "syntax_case_sensitive_replacement",
        expr={"$replaceOne": {"input": "hello", "find": "a", "Replacement": "b"}},
        error_code=REPLACE_UNKNOWN_FIELD_ERROR,
        msg="$replaceOne should reject case sensitive replacement",
    ),
    # Missing field precedence: input > find > replacement.
    ReplaceOneTest(
        "syntax_missing_input_and_find",
        expr={"$replaceOne": {"replacement": "b"}},
        error_code=REPLACE_MISSING_INPUT_ERROR,
        msg="$replaceOne should reject missing input and find",
    ),
    ReplaceOneTest(
        "syntax_missing_input_and_replacement",
        expr={"$replaceOne": {"find": "a"}},
        error_code=REPLACE_MISSING_INPUT_ERROR,
        msg="$replaceOne should reject missing input and replacement",
    ),
    ReplaceOneTest(
        "syntax_missing_find_and_replacement",
        expr={"$replaceOne": {"input": "hello"}},
        error_code=REPLACE_MISSING_FIND_ERROR,
        msg="$replaceOne should reject missing find and replacement",
    ),
    # Unknown field takes precedence over missing fields.
    ReplaceOneTest(
        "syntax_unknown_precedes_missing",
        expr={"$replaceOne": {"extra": 1}},
        error_code=REPLACE_UNKNOWN_FIELD_ERROR,
        msg="$replaceOne should reject unknown precedes missing",
    ),
    # Unknown field takes precedence over type errors.
    ReplaceOneTest(
        "syntax_unknown_precedes_type_error",
        expr={"$replaceOne": {"input": 123, "find": "a", "replacement": "b", "extra": 1}},
        error_code=REPLACE_UNKNOWN_FIELD_ERROR,
        msg="$replaceOne should reject unknown precedes type error",
    ),
]

REPLACEONE_INVALID_ARGS_ALL_TESTS = (
    REPLACEONE_TYPE_PRECEDENCE_TESTS
    + REPLACEONE_BARE_DOLLAR_TESTS
    + REPLACEONE_DOUBLE_DOLLAR_TESTS
    + REPLACEONE_NON_OBJECT_TESTS
    + REPLACEONE_FIELD_VALIDATION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_INVALID_ARGS_ALL_TESTS))
def test_replaceone_invalid_args_cases(collection, test_case: ReplaceOneTest):
    """Test $replaceOne invalid argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
