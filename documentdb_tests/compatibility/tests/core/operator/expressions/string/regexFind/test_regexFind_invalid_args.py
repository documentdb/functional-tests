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

from .utils.regexFind_common import (
    RegexFindTest,
    _expr,
)

# Property [Syntax Validation]: missing required fields or unknown fields produce errors.
REGEXFIND_SYNTAX_ERROR_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "syntax_non_object_string",
        expr={"$regexFind": "string"},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFind should reject string as argument",
    ),
    RegexFindTest(
        "syntax_non_object_array",
        expr={"$regexFind": ["array"]},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFind should reject array as argument",
    ),
    RegexFindTest(
        "syntax_non_object_null",
        expr={"$regexFind": None},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFind should reject null as argument",
    ),
    RegexFindTest(
        "syntax_non_object_int",
        expr={"$regexFind": 42},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFind should reject int as argument",
    ),
    RegexFindTest(
        "syntax_non_object_bool",
        expr={"$regexFind": True},
        error_code=REGEX_NON_OBJECT_ERROR,
        msg="$regexFind should reject bool as argument",
    ),
    RegexFindTest(
        "syntax_empty_object",
        expr={"$regexFind": {}},
        error_code=REGEX_MISSING_INPUT_ERROR,
        msg="$regexFind should reject empty object",
    ),
    RegexFindTest(
        "syntax_missing_input",
        expr={"$regexFind": {"regex": "abc"}},
        error_code=REGEX_MISSING_INPUT_ERROR,
        msg="$regexFind should reject missing input field",
    ),
    RegexFindTest(
        "syntax_missing_regex",
        expr={"$regexFind": {"input": "abc"}},
        error_code=REGEX_MISSING_REGEX_ERROR,
        msg="$regexFind should reject missing regex field",
    ),
    RegexFindTest(
        "syntax_unknown_field",
        expr={"$regexFind": {"input": "abc", "regex": "abc", "bogus": 1}},
        error_code=REGEX_UNKNOWN_FIELD_ERROR,
        msg="$regexFind should reject unknown fields",
    ),
]

# Property [Options Placement]: when regex is a BSON Regex with flags, specifying the options
# field produces an error, even if the flags are equivalent or options is empty.
REGEXFIND_OPTIONS_CONFLICT_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "options_conflict_same_flags",
        input="hello",
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFind should error when options duplicates BSON flags",
    ),
    RegexFindTest(
        "options_conflict_different_flags",
        input="hello",
        regex=Regex("hello", "i"),
        options="m",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFind should error when options differs from BSON flags",
    ),
    RegexFindTest(
        "options_conflict_empty_options",
        input="hello",
        regex=Regex("hello", "i"),
        options="",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFind should error on empty options with BSON flags",
    ),
]

# Property [Type Strictness - pattern]: invalid regex pattern produces an error.
REGEXFIND_BAD_PATTERN_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "type_bad_pattern_bracket",
        input="abc",
        regex="[invalid",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFind should reject unclosed bracket in pattern",
    ),
    RegexFindTest(
        "type_bad_pattern_paren",
        input="abc",
        regex="(unclosed",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFind should reject unclosed paren in pattern",
    ),
    RegexFindTest(
        "type_bad_pattern_var_lookbehind",
        input="abc",
        regex="(?<=a+)b",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFind should reject variable-length lookbehind",
    ),
]

# Property [Regex Pattern - null byte]: embedded null byte in regex pattern produces an error.
REGEXFIND_NULL_BYTE_PATTERN_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "type_null_byte_in_pattern",
        input="abc",
        regex="ab\x00c",
        error_code=REGEX_NULL_BYTE_ERROR,
        msg="$regexFind should reject null byte in regex pattern",
    ),
]

# Property [Type Strictness - option char]: unrecognized option character produces an error.
# Leading/trailing whitespace and mixed valid/invalid flags also produce errors.
REGEXFIND_BAD_OPTION_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "type_bad_option",
        input="abc",
        regex="abc",
        options="z",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFind should reject unrecognized option character",
    ),
    RegexFindTest(
        "type_bad_option_leading_whitespace",
        input="abc",
        regex="abc",
        options=" i",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFind should reject leading whitespace in options",
    ),
    RegexFindTest(
        "type_bad_option_trailing_whitespace",
        input="abc",
        regex="abc",
        options="i ",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFind should reject trailing whitespace in options",
    ),
    RegexFindTest(
        "type_bad_option_mixed_valid_invalid",
        input="abc",
        regex="abc",
        options="ig",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFind should reject mix of valid and invalid options",
    ),
    RegexFindTest(
        "type_bad_option_uppercase_I",
        input="abc",
        regex="abc",
        options="I",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFind should reject uppercase option character",
    ),
]

# Property [Null Byte in Options]: null byte in options string produces a distinct error.
REGEXFIND_OPTIONS_NULL_BYTE_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "type_null_byte_in_options",
        input="abc",
        regex="abc",
        options="i\x00m",
        error_code=REGEX_OPTIONS_NULL_BYTE_ERROR,
        msg="$regexFind should reject null byte in options string",
    ),
]

# Property [Dollar Sign Error]: a bare "$" is interpreted as a field path and "$$" is interpreted
# as an empty variable name.
REGEXFIND_DOLLAR_ERROR_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "dollar_bare_input",
        input="$",
        regex="abc",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexFind should reject bare '$' as input field path",
    ),
    RegexFindTest(
        "dollar_bare_regex",
        input="hello",
        regex="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexFind should reject bare '$' as regex field path",
    ),
    RegexFindTest(
        "dollar_bare_options",
        input="hello",
        regex="abc",
        options="$",
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$regexFind should reject bare '$' as options field path",
    ),
    RegexFindTest(
        "dollar_double_input",
        input="$$",
        regex="abc",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexFind should reject '$$' as empty variable in input",
    ),
    RegexFindTest(
        "dollar_double_regex",
        input="hello",
        regex="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexFind should reject '$$' as empty variable in regex",
    ),
    RegexFindTest(
        "dollar_double_options",
        input="hello",
        regex="abc",
        options="$$",
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$regexFind should reject '$$' as empty variable in options",
    ),
]

REGEXFIND_INVALID_ARGS_ALL_TESTS = (
    REGEXFIND_SYNTAX_ERROR_TESTS
    + REGEXFIND_OPTIONS_CONFLICT_TESTS
    + REGEXFIND_BAD_PATTERN_TESTS
    + REGEXFIND_NULL_BYTE_PATTERN_TESTS
    + REGEXFIND_BAD_OPTION_TESTS
    + REGEXFIND_OPTIONS_NULL_BYTE_TESTS
    + REGEXFIND_DOLLAR_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFIND_INVALID_ARGS_ALL_TESTS))
def test_regexfind_cases(collection, test_case: RegexFindTest):
    """Test $regexFind invalid argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
