from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    REGEX_BAD_OPTION_ERROR,
    REGEX_BAD_PATTERN_ERROR,
    REGEX_MISSING_INPUT_ERROR,
    REGEX_MISSING_REGEX_ERROR,
    REGEX_NON_OBJECT_ERROR,
    REGEX_NULL_BYTE_ERROR,
    REGEX_OPTIONS_NULL_BYTE_ERROR,
    REGEX_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexFindAll.utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Syntax Validation]: missing required fields or unknown fields produce errors.
REGEXFINDALL_SYNTAX_ERROR_TESTS: list[RegexFindAllTest] = [
    # Non-object argument.
    RegexFindAllTest(
        "syntax_non_object_string",
        expr={"$regexFindAll": "string"},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFindAll should reject string as argument",
    ),
    RegexFindAllTest(
        "syntax_non_object_array",
        expr={"$regexFindAll": ["array"]},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFindAll should reject array as argument",
    ),
    RegexFindAllTest(
        "syntax_non_object_null",
        expr={"$regexFindAll": None},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFindAll should reject null as argument",
    ),
    RegexFindAllTest(
        "syntax_non_object_int",
        expr={"$regexFindAll": 42},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFindAll should reject int as argument",
    ),
    RegexFindAllTest(
        "syntax_non_object_bool",
        expr={"$regexFindAll": True},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFindAll should reject bool as argument",
    ),
    # Empty object produces missing input error.
    RegexFindAllTest(
        "syntax_empty_object",
        expr={"$regexFindAll": {}},
        error_code=REGEX_MISSING_INPUT_ERROR,
        msg="$regexFindAll should reject empty object with missing input error",
    ),
    RegexFindAllTest(
        "syntax_missing_input",
        expr={"$regexFindAll": {"regex": "abc"}},
        error_code=REGEX_MISSING_INPUT_ERROR,
        msg="$regexFindAll should reject object missing input field",
    ),
    RegexFindAllTest(
        "syntax_missing_regex",
        expr={"$regexFindAll": {"input": "abc"}},
        error_code=REGEX_MISSING_REGEX_ERROR,
        msg="$regexFindAll should reject object missing regex field",
    ),
    RegexFindAllTest(
        "syntax_unknown_field",
        expr={"$regexFindAll": {"input": "abc", "regex": "abc", "bogus": 1}},
        error_code=REGEX_UNKNOWN_FIELD_ERROR,
        msg="$regexFindAll should reject unknown field in argument object",
    ),
]


# Property [Type Strictness - pattern]: invalid regex pattern produces an error.
REGEXFINDALL_BAD_PATTERN_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "type_bad_pattern_bracket",
        input="abc",
        regex="[invalid",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFindAll should reject unclosed bracket in regex pattern",
    ),
    RegexFindAllTest(
        "type_bad_pattern_paren",
        input="abc",
        regex="(unclosed",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFindAll should reject unclosed parenthesis in regex pattern",
    ),
    RegexFindAllTest(
        "type_bad_pattern_var_lookbehind",
        input="abc",
        regex="(?<=a+)b",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFindAll should reject variable-length lookbehind in regex pattern",
    ),
]

# Property [Regex Pattern - null byte]: embedded null byte in regex pattern produces an error.
REGEXFINDALL_NULL_BYTE_PATTERN_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "type_null_byte_in_pattern",
        input="abc",
        regex="ab\x00c",
        error_code=REGEX_NULL_BYTE_ERROR,
        msg="$regexFindAll should reject embedded null byte in regex pattern",
    ),
]

# Property [Type Strictness - option char]: unrecognized option character produces an error.
# Leading/trailing whitespace and mixed valid/invalid flags also produce errors.
REGEXFINDALL_BAD_OPTION_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "type_bad_option",
        input="abc",
        regex="abc",
        options="z",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFindAll should reject unrecognized option character 'z'",
    ),
    # Leading whitespace treated as invalid flag.
    RegexFindAllTest(
        "type_bad_option_leading_whitespace",
        input="abc",
        regex="abc",
        options=" i",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFindAll should reject leading whitespace in options",
    ),
    # Trailing whitespace treated as invalid flag.
    RegexFindAllTest(
        "type_bad_option_trailing_whitespace",
        input="abc",
        regex="abc",
        options="i ",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFindAll should reject trailing whitespace in options",
    ),
    # Mix of valid and invalid flags.
    RegexFindAllTest(
        "type_bad_option_mixed_valid_invalid",
        input="abc",
        regex="abc",
        options="ig",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFindAll should reject options containing mix of valid and invalid flags",
    ),
    # Uppercase valid flags are rejected.
    RegexFindAllTest(
        "type_bad_option_uppercase_I",
        input="abc",
        regex="abc",
        options="I",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFindAll should reject uppercase 'I' as option flag",
    ),
]

# Property [Null Byte in Options]: null byte in options string produces a distinct error.
REGEXFINDALL_OPTIONS_NULL_BYTE_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "type_null_byte_in_options",
        input="abc",
        regex="abc",
        options="i\x00m",
        error_code=REGEX_OPTIONS_NULL_BYTE_ERROR,
        msg="$regexFindAll should reject embedded null byte in options string",
    ),
]


# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
REGEXFINDALL_DOLLAR_ERROR_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "dollar_bare_input",
        input="$",
        regex="abc",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexFindAll should reject bare '$' as input field path",
    ),
    RegexFindAllTest(
        "dollar_bare_regex",
        input="hello",
        regex="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexFindAll should reject bare '$' as regex field path",
    ),
    RegexFindAllTest(
        "dollar_bare_options",
        input="hello",
        regex="abc",
        options="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexFindAll should reject bare '$' as options field path",
    ),
    RegexFindAllTest(
        "dollar_double_input",
        input="$$",
        regex="abc",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexFindAll should reject '$$' as empty variable name in input",
    ),
    RegexFindAllTest(
        "dollar_double_regex",
        input="hello",
        regex="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexFindAll should reject '$$' as empty variable name in regex",
    ),
    RegexFindAllTest(
        "dollar_double_options",
        input="hello",
        regex="abc",
        options="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexFindAll should reject '$$' as empty variable name in options",
    ),
]

REGEXFINDALL_INVALID_ARGS_ALL_TESTS = (
    REGEXFINDALL_SYNTAX_ERROR_TESTS
    + REGEXFINDALL_BAD_PATTERN_TESTS
    + REGEXFINDALL_NULL_BYTE_PATTERN_TESTS
    + REGEXFINDALL_BAD_OPTION_TESTS
    + REGEXFINDALL_OPTIONS_NULL_BYTE_TESTS
    + REGEXFINDALL_DOLLAR_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_INVALID_ARGS_ALL_TESTS))
def test_regexfindall_invalid_args(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll syntax validation and invalid argument errors."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
