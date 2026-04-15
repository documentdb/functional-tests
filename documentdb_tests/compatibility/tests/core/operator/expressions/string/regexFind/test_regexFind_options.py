from __future__ import annotations

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.regexFind_common import (
    RegexFindTest,
    _expr,
)

# Property [Regex Options]: options field accepts i, m, s, x as a string or BSON Regex flags.
# Empty string, duplicates, and "u" (PCRE UTF-8 flag) are valid. Invalid BSON Regex flags are
# silently accepted.
REGEXFIND_OPTIONS_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "options_empty_string",
        input="hello",
        regex="hello",
        options="",
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind should accept empty string options",
    ),
    RegexFindTest(
        "options_i_case_insensitive",
        input="HELLO",
        regex="hello",
        options="i",
        expected={"match": "HELLO", "idx": 0, "captures": []},
        msg="$regexFind option 'i' should enable case-insensitive match",
    ),
    RegexFindTest(
        "options_m_multiline",
        input="line1\nline2",
        regex="^line2",
        options="m",
        expected={"match": "line2", "idx": 6, "captures": []},
        msg="$regexFind option 'm' should match ^ at line start",
    ),
    RegexFindTest(
        "options_m_crlf",
        input="line1\r\nline2",
        regex="^line2",
        options="m",
        expected={"match": "line2", "idx": 7, "captures": []},
        msg="$regexFind option 'm' should recognize CRLF as line ending",
    ),
    RegexFindTest(
        "options_s_dotall",
        input="line1\nline2",
        regex="line1.line2",
        options="s",
        expected={"match": "line1\nline2", "idx": 0, "captures": []},
        msg="$regexFind option 's' should make dot match newline",
    ),
    RegexFindTest(
        "options_x_extended",
        input="hello",
        regex="hel lo",
        options="x",
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind option 'x' should ignore whitespace in pattern",
    ),
    RegexFindTest(
        "options_u_silently_accepted",
        input="hello",
        regex="hello",
        options="u",
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind should silently accept 'u' option",
    ),
    RegexFindTest(
        "options_combined_im",
        input="HELLO\nWORLD",
        regex="^world",
        options="im",
        expected={"match": "WORLD", "idx": 6, "captures": []},
        msg="$regexFind should support combined 'im' options",
    ),
    RegexFindTest(
        "options_duplicate_ii",
        input="HELLO",
        regex="hello",
        options="ii",
        expected={"match": "HELLO", "idx": 0, "captures": []},
        msg="$regexFind should accept duplicate option characters",
    ),
    RegexFindTest(
        "options_bson_regex_flag_i",
        input="HELLO",
        regex=Regex("hello", "i"),
        expected={"match": "HELLO", "idx": 0, "captures": []},
        msg="$regexFind should honor BSON Regex 'i' flag",
    ),
    RegexFindTest(
        "options_bson_regex_flag_s",
        input="a\nb",
        regex=Regex("a.b", "s"),
        expected={"match": "a\nb", "idx": 0, "captures": []},
        msg="$regexFind should honor BSON Regex 's' flag",
    ),
    RegexFindTest(
        "options_bson_regex_flag_x",
        input="hello",
        regex=Regex("hel lo", "x"),
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind should honor BSON Regex 'x' flag",
    ),
    RegexFindTest(
        "options_bson_regex_invalid_flag_silent",
        input="hello",
        regex=Regex("hello", "z"),
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind should silently accept invalid BSON Regex flags",
    ),
    RegexFindTest(
        "options_all_four_combined",
        input="HELLO",
        regex="hel lo",
        options="imsx",
        expected={"match": "HELLO", "idx": 0, "captures": []},
        msg="$regexFind should support all four options combined",
    ),
    RegexFindTest(
        "options_no_conflict_null_options_with_flags",
        input="HELLO",
        regex=Regex("hello", "i"),
        options=None,
        expected={"match": "HELLO", "idx": 0, "captures": []},
        msg="$regexFind null options should not conflict with BSON flags",
    ),
    RegexFindTest(
        "options_no_conflict_no_flags_with_options",
        input="HELLO",
        regex=Regex("hello"),
        options="i",
        expected={"match": "HELLO", "idx": 0, "captures": []},
        msg="$regexFind should allow options with flagless BSON Regex",
    ),
    RegexFindTest(
        "options_no_conflict_empty_flags_with_options",
        input="HELLO",
        regex=Regex("hello", ""),
        options="i",
        expected={"match": "HELLO", "idx": 0, "captures": []},
        msg="$regexFind empty BSON flags should not conflict with options",
    ),
    RegexFindTest(
        "options_no_conflict_unrecognized_flag",
        input="hello",
        regex=Regex("hello", "z"),
        options="i",
        expected={"match": "hello", "idx": 0, "captures": []},
        msg="$regexFind unrecognized BSON flag should not conflict",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXFIND_OPTIONS_TESTS))
def test_regexfind_cases(collection, test_case: RegexFindTest):
    """Test $regexFind options cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
