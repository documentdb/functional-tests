from __future__ import annotations

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    REGEX_BAD_OPTION_ERROR,
    REGEX_BAD_PATTERN_ERROR,
    REGEX_INPUT_TYPE_ERROR,
    REGEX_OPTIONS_CONFLICT_ERROR,
    REGEX_OPTIONS_TYPE_ERROR,
    REGEX_REGEX_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

from .utils.regexFind_common import (
    RegexFindTest,
    _expr,
)

# Property [Type Error Precedence]: options type errors take precedence over null propagation.
# When both input and regex have wrong types, regex error wins. Wrong-type arguments error even
# when the other is null or missing.
REGEXFIND_PRECEDENCE_ERROR_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "precedence_options_over_null_input",
        input=None,
        regex="abc",
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind options type error should precede null input",
    ),
    RegexFindTest(
        "precedence_options_over_null_regex",
        input="abc",
        regex=None,
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind options type error should precede null regex",
    ),
    RegexFindTest(
        "precedence_options_over_both_null",
        input=None,
        regex=None,
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexFind options type error should precede both null",
    ),
    RegexFindTest(
        "precedence_regex_over_input",
        input=123,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind regex type error should precede input type error",
    ),
    RegexFindTest(
        "precedence_input_type_with_null_regex",
        input=123,
        regex=None,
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind should error on wrong-type input even with null regex",
    ),
    RegexFindTest(
        "precedence_regex_type_with_null_input",
        input=None,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind should error on wrong-type regex even with null input",
    ),
    RegexFindTest(
        "precedence_missing_input_wrong_regex",
        input=MISSING,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexFind missing input should not bypass regex type check",
    ),
    RegexFindTest(
        "precedence_wrong_input_missing_regex",
        input=123,
        regex=MISSING,
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexFind missing regex should not bypass input type check",
    ),
    RegexFindTest(
        "precedence_bad_option_over_null_input",
        input=None,
        regex="abc",
        options="z",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexFind bad option should precede null input",
    ),
    RegexFindTest(
        "precedence_bad_pattern_over_null_input",
        input=None,
        regex="[invalid",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexFind bad pattern should precede null input",
    ),
    RegexFindTest(
        "precedence_conflict_over_input_type",
        input=123,
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFind options conflict should precede input type error",
    ),
    RegexFindTest(
        "precedence_conflict_over_null_input",
        input=None,
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexFind options conflict should precede null input",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXFIND_PRECEDENCE_ERROR_TESTS))
def test_regexfind_cases(collection, test_case: RegexFindTest):
    """Test $regexFind error precedence cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
