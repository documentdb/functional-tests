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

from .utils.regexMatch_common import (
    RegexMatchTest,
    _expr,
)

# Property [Type Error Precedence]: options type errors take precedence over null propagation.
# When both input and regex have wrong types, regex error wins. Wrong-type arguments error even
# when the other is null or missing.
REGEXMATCH_PRECEDENCE_ERROR_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "precedence_options_over_null_input",
        input=None,
        regex="abc",
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexMatch options type error should precede null input",
    ),
    RegexMatchTest(
        "precedence_options_over_null_regex",
        input="abc",
        regex=None,
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexMatch options type error should precede null regex",
    ),
    RegexMatchTest(
        "precedence_options_over_both_null",
        input=None,
        regex=None,
        options=123,
        error_code=REGEX_OPTIONS_TYPE_ERROR,
        msg="$regexMatch options type error should precede both null",
    ),
    RegexMatchTest(
        "precedence_regex_over_input",
        input=123,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexMatch regex type error should precede input type error",
    ),
    RegexMatchTest(
        "precedence_input_type_with_null_regex",
        input=123,
        regex=None,
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexMatch should error on wrong-type input with null regex",
    ),
    RegexMatchTest(
        "precedence_regex_type_with_null_input",
        input=None,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexMatch should error on wrong-type regex with null input",
    ),
    RegexMatchTest(
        "precedence_missing_input_wrong_regex",
        input=MISSING,
        regex=123,
        error_code=REGEX_REGEX_TYPE_ERROR,
        msg="$regexMatch missing input should not bypass regex type check",
    ),
    RegexMatchTest(
        "precedence_wrong_input_missing_regex",
        input=123,
        regex=MISSING,
        error_code=REGEX_INPUT_TYPE_ERROR,
        msg="$regexMatch missing regex should not bypass input type check",
    ),
    RegexMatchTest(
        "precedence_bad_option_over_null_input",
        input=None,
        regex="abc",
        options="z",
        error_code=REGEX_BAD_OPTION_ERROR,
        msg="$regexMatch bad option should precede null input",
    ),
    RegexMatchTest(
        "precedence_bad_pattern_over_null_input",
        input=None,
        regex="[invalid",
        error_code=REGEX_BAD_PATTERN_ERROR,
        msg="$regexMatch bad pattern should precede null input",
    ),
    RegexMatchTest(
        "precedence_conflict_over_input_type",
        input=123,
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexMatch options conflict should precede input type error",
    ),
    RegexMatchTest(
        "precedence_conflict_over_null_input",
        input=None,
        regex=Regex("hello", "i"),
        options="i",
        error_code=REGEX_OPTIONS_CONFLICT_ERROR,
        msg="$regexMatch options conflict should precede null input",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXMATCH_PRECEDENCE_ERROR_TESTS))
def test_regexmatch_cases(collection, test_case: RegexMatchTest):
    """Test $regexMatch type error precedence cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
