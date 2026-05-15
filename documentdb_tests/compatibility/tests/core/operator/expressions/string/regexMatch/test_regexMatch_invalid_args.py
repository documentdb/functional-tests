from __future__ import annotations

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    REGEX_BAD_OPTION_ERROR,
    REGEX_BAD_PATTERN_ERROR,
    REGEX_MISSING_INPUT_ERROR,
    REGEX_MISSING_REGEX_ERROR,
    REGEX_NON_OBJECT_ERROR,
    REGEX_NULL_BYTE_ERROR,
    REGEX_OPTIONS_CONFLICT_ERROR,
    REGEX_OPTIONS_NULL_BYTE_ERROR,
    REGEX_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.regexMatch_common import (
    RegexMatchTest,
    _expr,
)

# Property [Syntax Validation]: missing required fields or unknown fields produce errors.
REGEXMATCH_SYNTAX_ERROR_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "syntax_non_object_string",
        expr={"$regexMatch": "string"},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexMatch should reject string as argument",
    ),
    RegexMatchTest(
        "syntax_non_object_array",
        expr={"$regexMatch": ["array"]},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexMatch should reject array as argument",
    ),
    RegexMatchTest(
        "syntax_non_object_null",
        expr={"$regexMatch": None},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexMatch should reject null as argument",
    ),
    RegexMatchTest(
        "syntax_non_object_int",
        expr={"$regexMatch": 42},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexMatch should reject int as argument",
    ),
    RegexMatchTest(
        "syntax_non_object_bool",
        expr={"$regexMatch": True},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexMatch should reject bool as argument",
    ),
    RegexMatchTest(
        "syntax_empty_object",
        expr={"$regexMatch": {}},
        error_code=REGEX_MISSING_INPUT_ERROR,
        msg="$regexMatch should reject empty object",
    ),
    RegexMatchTest(
        "syntax_missing_input",
        expr={"$regexMatch": {"regex": "abc"}},
        error_code=REGEX_MISSING_INPUT_ERROR,
        msg="$regexMatch should reject missing input field",
    ),
    RegexMatchTest(
        "syntax_missing_regex",
        expr={"$regexMatch": {"input": "abc"}},
        error_code=REGEX_MISSING_REGEX_ERROR,
        msg="$regexMatch should reject missing regex field",
    ),
    RegexMatchTest(
        "syntax_unknown_field",
        expr={"$regexMatch": {"input": "abc", "regex": "abc", "bogus": 1}},
        error_code=REGEX_UNKNOWN_FIELD_ERROR,
        msg="$regexMatch should reject unknown fields",
    ),
]


REGEXMATCH_OPTIONS_CONFLICT_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "options_conflict_same_flags",
        input="hello",
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexMatch should error when options duplicates BSON flags",
    ),
    RegexMatchTest(
        "options_conflict_different_flags",
        input="hello",
        regex=Regex("hello", "i"),
        options="m",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexMatch should error when options differs from BSON flags",
    ),
    RegexMatchTest(
        "options_conflict_empty_options",
        input="hello",
        regex=Regex("hello", "i"),
        options="",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexMatch should error on empty options with BSON flags",
    ),
]


# Property [Type Strictness - pattern]: invalid regex pattern produces an error.
REGEXMATCH_BAD_PATTERN_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "type_bad_pattern_bracket",
        input="abc",
        regex="[invalid",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexMatch should reject unclosed bracket in pattern",
    ),
    RegexMatchTest(
        "type_bad_pattern_paren",
        input="abc",
        regex="(unclosed",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexMatch should reject unclosed paren in pattern",
    ),
    RegexMatchTest(
        "type_bad_pattern_var_lookbehind",
        input="abc",
        regex="(?<=a+)b",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexMatch should reject variable-length lookbehind",
    ),
]

REGEXMATCH_NULL_BYTE_PATTERN_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "type_null_byte_in_pattern",
        input="abc",
        regex="ab\x00c",
        error_code=REGEX_NULL_BYTE_ERROR,
        msg="$regexMatch should reject null byte in regex pattern",
    ),
]

REGEXMATCH_BAD_OPTION_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "type_bad_option",
        input="abc",
        regex="abc",
        options="z",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexMatch should reject unrecognized option character",
    ),
    RegexMatchTest(
        "type_bad_option_leading_whitespace",
        input="abc",
        regex="abc",
        options=" i",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexMatch should reject leading whitespace in options",
    ),
    RegexMatchTest(
        "type_bad_option_trailing_whitespace",
        input="abc",
        regex="abc",
        options="i ",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexMatch should reject trailing whitespace in options",
    ),
    RegexMatchTest(
        "type_bad_option_mixed_valid_invalid",
        input="abc",
        regex="abc",
        options="ig",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexMatch should reject mix of valid and invalid options",
    ),
    RegexMatchTest(
        "type_bad_option_uppercase_I",
        input="abc",
        regex="abc",
        options="I",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexMatch should reject uppercase 'I' option",
    ),
    RegexMatchTest(
        "type_bad_option_uppercase_M",
        input="abc",
        regex="abc",
        options="M",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexMatch should reject uppercase 'M' option",
    ),
]

REGEXMATCH_OPTIONS_NULL_BYTE_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "type_null_byte_in_options",
        input="abc",
        regex="abc",
        options="i\x00m",
        error_code=REGEX_OPTIONS_NULL_BYTE_ERROR,
        msg="$regexMatch should reject null byte in options string",
    ),
]


# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
REGEXMATCH_DOLLAR_ERROR_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "dollar_bare_input",
        input="$",
        regex="abc",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexMatch should reject bare '$' as input field path",
    ),
    RegexMatchTest(
        "dollar_bare_regex",
        input="hello",
        regex="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexMatch should reject bare '$' as regex field path",
    ),
    RegexMatchTest(
        "dollar_bare_options",
        input="hello",
        regex="abc",
        options="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexMatch should reject bare '$' as options field path",
    ),
    RegexMatchTest(
        "dollar_double_input",
        input="$$",
        regex="abc",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexMatch should reject '$$' as empty variable in input",
    ),
    RegexMatchTest(
        "dollar_double_regex",
        input="hello",
        regex="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexMatch should reject '$$' as empty variable in regex",
    ),
    RegexMatchTest(
        "dollar_double_options",
        input="hello",
        regex="abc",
        options="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexMatch should reject '$$' as empty variable in options",
    ),
]

REGEXMATCH_INVALID_ARGS_ALL_TESTS = (
    REGEXMATCH_SYNTAX_ERROR_TESTS
    + REGEXMATCH_OPTIONS_CONFLICT_TESTS
    + REGEXMATCH_BAD_PATTERN_TESTS
    + REGEXMATCH_NULL_BYTE_PATTERN_TESTS
    + REGEXMATCH_BAD_OPTION_TESTS
    + REGEXMATCH_OPTIONS_NULL_BYTE_TESTS
    + REGEXMATCH_DOLLAR_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXMATCH_INVALID_ARGS_ALL_TESTS))
def test_regexmatch_cases(collection, test_case: RegexMatchTest):
    """Test $regexMatch invalid argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
