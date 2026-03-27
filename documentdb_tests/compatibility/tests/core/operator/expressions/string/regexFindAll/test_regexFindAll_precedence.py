from __future__ import annotations

import pytest
from bson import Regex

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    REGEX_BAD_OPTION_ERROR,
    REGEX_BAD_PATTERN_ERROR,
    REGEX_INPUT_TYPE_ERROR,
    REGEX_OPTIONS_CONFLICT_ERROR,
    REGEX_OPTIONS_TYPE_ERROR,
    REGEX_REGEX_TYPE_ERROR,
)
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexFindAll.utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Null Precedence]: null propagation from regex takes precedence over bad option flag
# validation.
REGEXFINDALL_PRECEDENCE_SUCCESS_TESTS: list[RegexFindAllTest] = [
    # Null regex takes precedence over bad option flag validation.
    RegexFindAllTest(
        "precedence_null_regex_over_bad_option",
        input="abc",
        regex=None,
        options="z",
        expected=[],
        msg="$regexFindAll null regex should take precedence over invalid option flag",
    ),
]


# Property [Options Placement]: when regex is a BSON Regex with flags, specifying the options field
# produces an error, even if the flags are equivalent or options is empty.
REGEXFINDALL_OPTIONS_CONFLICT_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "options_conflict_same_flags",
        input="hello",
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFindAll should reject options field when BSON Regex has same flags",
    ),
    RegexFindAllTest(
        "options_conflict_different_flags",
        input="hello",
        regex=Regex("hello", "i"),
        options="m",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFindAll should reject options field when BSON Regex has different flags",
    ),
    RegexFindAllTest(
        "options_conflict_empty_options",
        input="hello",
        regex=Regex("hello", "i"),
        options="",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFindAll should reject empty options field when BSON Regex has flags",
    ),
]


# Property [Type Error Precedence]: options type errors take precedence over null propagation. When
# both input and regex have wrong types, regex error wins. Wrong-type arguments error even when the
# other is null or missing.
REGEXFINDALL_PRECEDENCE_ERROR_TESTS: list[RegexFindAllTest] = [
    # Options type error takes precedence over null input.
    RegexFindAllTest(
        "precedence_options_over_null_input",
        input=None,
        regex="abc",
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFindAll options type error should take precedence over null input",
    ),
    # Options type error takes precedence over null regex.
    RegexFindAllTest(
        "precedence_options_over_null_regex",
        input="abc",
        regex=None,
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFindAll options type error should take precedence over null regex",
    ),
    # Options type error takes precedence over both null.
    RegexFindAllTest(
        "precedence_options_over_both_null",
        input=None,
        regex=None,
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFindAll options type error should take precedence over both null input/regex",
    ),
    # Both input and regex wrong type: regex error wins.
    RegexFindAllTest(
        "precedence_regex_over_input",
        input=123,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFindAll regex type error should take precedence over input type error",
    ),
    # Wrong-type input still errors when regex is null.
    RegexFindAllTest(
        "precedence_input_type_with_null_regex",
        input=123,
        regex=None,
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFindAll should report input type error even when regex is null",
    ),
    # Wrong-type regex still errors when input is null.
    RegexFindAllTest(
        "precedence_regex_type_with_null_input",
        input=None,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFindAll should report regex type error even when input is null",
    ),
    # Missing input does not bypass type check of regex.
    RegexFindAllTest(
        "precedence_missing_input_wrong_regex",
        input=MISSING,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFindAll should report regex type error even when input is missing",
    ),
    # Missing regex does not bypass type check of input.
    RegexFindAllTest(
        "precedence_wrong_input_missing_regex",
        input=123,
        regex=MISSING,
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFindAll should report input type error even when regex is missing",
    ),
    # Bad option flag takes precedence over null input.
    RegexFindAllTest(
        "precedence_bad_option_over_null_input",
        input=None,
        regex="abc",
        options="z",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFindAll bad option flag should take precedence over null input",
    ),
    # Invalid regex pattern takes precedence over null input.
    RegexFindAllTest(
        "precedence_bad_pattern_over_null_input",
        input=None,
        regex="[invalid",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFindAll bad pattern error should take precedence over null input",
    ),
    # Options conflict takes precedence over wrong-type input.
    RegexFindAllTest(
        "precedence_conflict_over_input_type",
        input=123,
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFindAll options conflict should take precedence over input type error",
    ),
    # Options conflict takes precedence over null input.
    RegexFindAllTest(
        "precedence_conflict_over_null_input",
        input=None,
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFindAll options conflict should take precedence over null input",
    ),
]

REGEXFINDALL_PRECEDENCE_ALL_TESTS = (
    REGEXFINDALL_PRECEDENCE_SUCCESS_TESTS
    + REGEXFINDALL_OPTIONS_CONFLICT_TESTS
    + REGEXFINDALL_PRECEDENCE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_PRECEDENCE_ALL_TESTS))
def test_regexfindall_precedence(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll error precedence and options conflict."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
