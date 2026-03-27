from __future__ import annotations

import pytest
from bson import Regex

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexMatch.utils.regexMatch_common import (
    RegexMatchTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Regex Options]: options field accepts i, m, s, x as a string or BSON Regex flags.
# Empty string, duplicates, and "u" (PCRE UTF-8 flag) are valid. Invalid BSON Regex flags are
# silently accepted.
REGEXMATCH_OPTIONS_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "options_empty_string",
        input="hello",
        regex="hello",
        options="",
        expected=True,
        msg="$regexMatch should accept empty string options",
    ),
    RegexMatchTest(
        "options_i_case_insensitive",
        input="HELLO",
        regex="hello",
        options="i",
        expected=True,
        msg="$regexMatch option 'i' should enable case-insensitive match",
    ),
    RegexMatchTest(
        "options_m_multiline",
        input="line1\nline2",
        regex="^line2",
        options="m",
        expected=True,
        msg="$regexMatch option 'm' should match ^ at line start",
    ),
    RegexMatchTest(
        "options_m_crlf",
        input="line1\r\nline2",
        regex="^line2",
        options="m",
        expected=True,
        msg="$regexMatch option 'm' should recognize CRLF as line ending",
    ),
    RegexMatchTest(
        "options_s_dotall",
        input="line1\nline2",
        regex="line1.line2",
        options="s",
        expected=True,
        msg="$regexMatch option 's' should make dot match newline",
    ),
    RegexMatchTest(
        "options_x_extended",
        input="hello",
        regex="hel lo",
        options="x",
        expected=True,
        msg="$regexMatch option 'x' should ignore whitespace in pattern",
    ),
    RegexMatchTest(
        "options_u_silently_accepted",
        input="hello",
        regex="hello",
        options="u",
        expected=True,
        msg="$regexMatch should silently accept 'u' option",
    ),
    RegexMatchTest(
        "options_combined_im",
        input="HELLO\nWORLD",
        regex="^world",
        options="im",
        expected=True,
        msg="$regexMatch should support combined 'im' options",
    ),
    RegexMatchTest(
        "options_duplicate_ii",
        input="HELLO",
        regex="hello",
        options="ii",
        expected=True,
        msg="$regexMatch should accept duplicate option characters",
    ),
    RegexMatchTest(
        "options_bson_regex_flag_i",
        input="HELLO",
        regex=Regex("hello", "i"),
        expected=True,
        msg="$regexMatch should honor BSON Regex 'i' flag",
    ),
    RegexMatchTest(
        "options_bson_regex_flag_s",
        input="a\nb",
        regex=Regex("a.b", "s"),
        expected=True,
        msg="$regexMatch should honor BSON Regex 's' flag",
    ),
    RegexMatchTest(
        "options_bson_regex_flag_x",
        input="hello",
        regex=Regex("hel lo", "x"),
        expected=True,
        msg="$regexMatch should honor BSON Regex 'x' flag",
    ),
    RegexMatchTest(
        "options_bson_regex_invalid_flag_silent",
        input="hello",
        regex=Regex("hello", "z"),
        expected=True,
        msg="$regexMatch should silently accept invalid BSON Regex flags",
    ),
    RegexMatchTest(
        "options_all_four_combined",
        input="HELLO",
        regex="hel lo",
        options="imsx",
        expected=True,
        msg="$regexMatch should support all four options combined",
    ),
    RegexMatchTest(
        "options_no_conflict_null_options_with_flags",
        input="HELLO",
        regex=Regex("hello", "i"),
        options=None,
        expected=True,
        msg="$regexMatch null options should not conflict with BSON flags",
    ),
    RegexMatchTest(
        "options_no_conflict_no_flags_with_options",
        input="HELLO",
        regex=Regex("hello"),
        options="i",
        expected=True,
        msg="$regexMatch should allow options with flagless BSON Regex",
    ),
    RegexMatchTest(
        "options_no_conflict_empty_flags_with_options",
        input="HELLO",
        regex=Regex("hello", ""),
        options="i",
        expected=True,
        msg="$regexMatch empty BSON flags should not conflict with options",
    ),
]


# Property [Options Conflict - no conflict]: BSON Regex with only unrecognized flags.
REGEXMATCH_OPTIONS_NO_CONFLICT_TESTS: list[RegexMatchTest] = [
    RegexMatchTest(
        "options_no_conflict_unrecognized_flag",
        input="hello",
        regex=Regex("hello", "z"),
        options="i",
        expected=True,
        msg="$regexMatch unrecognized BSON flag should not conflict",
    ),
]

REGEXMATCH_OPTIONS_ALL_TESTS = REGEXMATCH_OPTIONS_TESTS + REGEXMATCH_OPTIONS_NO_CONFLICT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(REGEXMATCH_OPTIONS_ALL_TESTS))
def test_regexmatch_cases(collection, test_case: RegexMatchTest):
    """Test $regexMatch options cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
