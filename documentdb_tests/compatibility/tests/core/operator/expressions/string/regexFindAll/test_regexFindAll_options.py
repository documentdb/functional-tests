from __future__ import annotations

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)

# Property [Regex Options]: options field accepts i, m, s, x as a string or BSON Regex flags. Empty
# string, duplicates, and "u" (PCRE UTF-8 flag) are valid. Invalid BSON Regex flags are silently
# accepted.
REGEXFINDALL_OPTIONS_TESTS: list[RegexFindAllTest] = [
    # Empty string options is valid and means no options.
    RegexFindAllTest(
        "options_empty_string",
        input="hello",
        regex="hello",
        options="",
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should accept empty string as valid options",
    ),
    # i: case-insensitive.
    RegexFindAllTest(
        "options_i_case_insensitive",
        input="HELLO",
        regex="hello",
        options="i",
        expected=[{"match": "HELLO", "idx": 0, "captures": []}],
        msg="$regexFindAll should match case-insensitively with 'i' option",
    ),
    # m: multiline, ^ matches start of each line.
    RegexFindAllTest(
        "options_m_multiline",
        input="line1\nline2",
        regex="^line2",
        options="m",
        expected=[{"match": "line2", "idx": 6, "captures": []}],
        msg="$regexFindAll should match ^ at start of each line with 'm' option",
    ),
    # m: \r\n recognized as line ending.
    RegexFindAllTest(
        "options_m_crlf",
        input="line1\r\nline2",
        regex="^line2",
        options="m",
        expected=[{"match": "line2", "idx": 7, "captures": []}],
        msg="$regexFindAll should recognize \\r\\n as line ending with 'm' option",
    ),
    # s: dotAll, . matches newline.
    RegexFindAllTest(
        "options_s_dotall",
        input="line1\nline2",
        regex="line1.line2",
        options="s",
        expected=[{"match": "line1\nline2", "idx": 0, "captures": []}],
        msg="$regexFindAll should match dot against newline with 's' option",
    ),
    # x: extended, whitespace in pattern is ignored.
    RegexFindAllTest(
        "options_x_extended",
        input="hello",
        regex="hel lo",
        options="x",
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should ignore whitespace in pattern with 'x' option",
    ),
    # u: PCRE UTF-8 flag. Unlike truly invalid flags (e.g. "g", "z") which produce
    # REGEX_BAD_OPTION_ERROR, "u" is silently accepted because the underlying PCRE engine
    # recognizes it. It has no observable effect since the server already operates in UTF-8 mode.
    RegexFindAllTest(
        "options_u_silently_accepted",
        input="hello",
        regex="hello",
        options="u",
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should silently accept 'u' option without error",
    ),
    # Combined options.
    RegexFindAllTest(
        "options_combined_im",
        input="HELLO\nWORLD",
        regex="^world",
        options="im",
        expected=[{"match": "WORLD", "idx": 6, "captures": []}],
        msg="$regexFindAll should apply combined 'im' options together",
    ),
    # Duplicate option characters accepted.
    RegexFindAllTest(
        "options_duplicate_ii",
        input="HELLO",
        regex="hello",
        options="ii",
        expected=[{"match": "HELLO", "idx": 0, "captures": []}],
        msg="$regexFindAll should accept duplicate option characters",
    ),
    # BSON Regex flag i (case-insensitive).
    RegexFindAllTest(
        "options_bson_regex_flag_i",
        input="HELLO",
        regex=Regex("hello", "i"),
        expected=[{"match": "HELLO", "idx": 0, "captures": []}],
        msg="$regexFindAll should apply case-insensitive flag from BSON Regex",
    ),
    # BSON Regex flag s (dotAll).
    RegexFindAllTest(
        "options_bson_regex_flag_s",
        input="a\nb",
        regex=Regex("a.b", "s"),
        expected=[{"match": "a\nb", "idx": 0, "captures": []}],
        msg="$regexFindAll should apply dotAll flag from BSON Regex",
    ),
    # BSON Regex flag x (extended).
    RegexFindAllTest(
        "options_bson_regex_flag_x",
        input="hello",
        regex=Regex("hel lo", "x"),
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should apply extended flag from BSON Regex",
    ),
    # Invalid flags in a BSON Regex object are silently accepted (the server does not
    # validate BSON Regex flags the same way it validates the options string).
    RegexFindAllTest(
        "options_bson_regex_invalid_flag_silent",
        input="hello",
        regex=Regex("hello", "z"),
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should silently accept invalid flags in BSON Regex",
    ),
    # All four options combined as string.
    RegexFindAllTest(
        "options_all_four_combined",
        input="HELLO",
        regex="hel lo",
        options="imsx",
        expected=[{"match": "HELLO", "idx": 0, "captures": []}],
        msg="$regexFindAll should apply all four options combined as 'imsx'",
    ),
    # Null options does not count as "specifying options", so no conflict with BSON Regex flags.
    RegexFindAllTest(
        "options_no_conflict_null_options_with_flags",
        input="HELLO",
        regex=Regex("hello", "i"),
        options=None,
        expected=[{"match": "HELLO", "idx": 0, "captures": []}],
        msg="$regexFindAll should not conflict when options is null and BSON Regex has flags",
    ),
    # BSON Regex with no flags, options field provides the option.
    RegexFindAllTest(
        "options_no_conflict_no_flags_with_options",
        input="HELLO",
        regex=Regex("hello"),
        options="i",
        expected=[{"match": "HELLO", "idx": 0, "captures": []}],
        msg="$regexFindAll should accept options field when BSON Regex has no flags",
    ),
    # BSON Regex with empty flags combined with non-empty options is accepted.
    RegexFindAllTest(
        "options_no_conflict_empty_flags_with_options",
        input="HELLO",
        regex=Regex("hello", ""),
        options="i",
        expected=[{"match": "HELLO", "idx": 0, "captures": []}],
        msg="$regexFindAll should accept options field when BSON Regex has empty flags",
    ),
]


# Property [Options Conflict - no conflict]: BSON Regex with only unrecognized flags does not
# conflict with the options field.
REGEXFINDALL_OPTIONS_NO_CONFLICT_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "options_no_conflict_unrecognized_flag",
        input="hello",
        regex=Regex("hello", "z"),
        options="i",
        expected=[{"match": "hello", "idx": 0, "captures": []}],
        msg="$regexFindAll should not conflict when BSON Regex has only unrecognized flags",
    ),
]

REGEXFINDALL_OPTIONS_ALL_TESTS = REGEXFINDALL_OPTIONS_TESTS + REGEXFINDALL_OPTIONS_NO_CONFLICT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_OPTIONS_ALL_TESTS))
def test_regexfindall_options(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll regex options behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
