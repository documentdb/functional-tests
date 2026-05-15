from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.regexFind_common import (
    RegexFindTest,
    _expr,
)

# Property [First Match Only]: only the first match in the input string is returned.
REGEXFIND_FIRST_MATCH_TESTS: list[RegexFindTest] = [
    # Second match is "456" but only the first should be returned.
    RegexFindTest(
        "first_match_two_numeric",
        input="abc123def456",
        regex="[0-9]+",
        expected={"match": "123", "idx": 3, "captures": []},
        msg="$regexFind should return only the first numeric match",
    ),
    # Greedy quantifier matches longest at first position.
    RegexFindTest(
        "first_match_greedy",
        input="aabab",
        regex="a.*b",
        expected={"match": "aabab", "idx": 0, "captures": []},
        msg="$regexFind should return greedy match at first position",
    ),
    # Lazy quantifier matches shortest at first position.
    RegexFindTest(
        "first_match_lazy",
        input="aabab",
        regex="a.*?b",
        expected={"match": "aab", "idx": 0, "captures": []},
        msg="$regexFind should return lazy match at first position",
    ),
]

# Property [idx Code Point Semantics]: idx counts Unicode code points, not bytes. Each character
# contributes 1 regardless of UTF-8 byte width.
REGEXFIND_IDX_CODEPOINT_TESTS: list[RegexFindTest] = [
    # é (U+00E9) is 2 bytes. Byte index would be 2, codepoint index is 1.
    RegexFindTest(
        "idx_cp_2byte_prefix",
        input="\u00e9abc",
        regex="abc",
        expected={"match": "abc", "idx": 1, "captures": []},
        msg="$regexFind idx should count 2-byte char as one codepoint",
    ),
    # 日 (U+65E5) is 3 bytes. Byte index would be 3, codepoint index is 1.
    RegexFindTest(
        "idx_cp_3byte_prefix",
        input="日abc",
        regex="abc",
        expected={"match": "abc", "idx": 1, "captures": []},
        msg="$regexFind idx should count 3-byte char as one codepoint",
    ),
    # 🎉 (U+1F389) is 4 bytes. Byte index would be 4, codepoint index is 1.
    RegexFindTest(
        "idx_cp_4byte_prefix",
        input="🎉abc",
        regex="abc",
        expected={"match": "abc", "idx": 1, "captures": []},
        msg="$regexFind idx should count 4-byte char as one codepoint",
    ),
    # Mix of 2-byte, 3-byte, and 4-byte chars. Byte index would be 9, codepoint index is 3.
    RegexFindTest(
        "idx_cp_mixed_byte_widths",
        input="\u00e9日🎉abc",
        regex="abc",
        expected={"match": "abc", "idx": 3, "captures": []},
        msg="$regexFind idx should count mixed multi-byte chars as codepoints",
    ),
    # Three 3-byte CJK chars. Byte index would be 9, codepoint index is 3.
    RegexFindTest(
        "idx_cp_cjk_prefix",
        input="日本語abc",
        regex="abc",
        expected={"match": "abc", "idx": 3, "captures": []},
        msg="$regexFind idx should count CJK chars as codepoints",
    ),
    # Combining mark (e + U+0301) is two codepoints, not one. idx would be 1 if normalized
    # to precomposed U+00E9.
    RegexFindTest(
        "idx_cp_combining_mark",
        input="e\u0301abc",
        regex="abc",
        expected={"match": "abc", "idx": 2, "captures": []},
        msg="$regexFind idx should count combining mark as separate codepoint",
    ),
]

# Property [Captures Behavior]: captures array length equals the number of capture groups, in
# pattern order. Unmatched branches produce null. Non-capturing groups are excluded. Nested
# groups are each represented.
REGEXFIND_CAPTURES_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "captures_single_group",
        input="abc123",
        regex="([0-9]+)",
        expected={"match": "123", "idx": 3, "captures": ["123"]},
        msg="$regexFind should capture single group",
    ),
    # Order matches left-to-right group appearance.
    RegexFindTest(
        "captures_two_groups_order",
        input="John Smith",
        regex="(\\w+) (\\w+)",
        expected={"match": "John Smith", "idx": 0, "captures": ["John", "Smith"]},
        msg="$regexFind should capture groups in left-to-right order",
    ),
    # Second alternation branch unmatched produces null in that position.
    RegexFindTest(
        "captures_unmatched_branch",
        input="cat",
        regex="(cat)|(dog)",
        expected={"match": "cat", "idx": 0, "captures": ["cat", None]},
        msg="$regexFind should produce null for unmatched alternation branch",
    ),
    # Non-capturing group excluded from captures.
    RegexFindTest(
        "captures_non_capturing_excluded",
        input="abc123",
        regex="(?:abc)([0-9]+)",
        expected={"match": "abc123", "idx": 0, "captures": ["123"]},
        msg="$regexFind should exclude non-capturing group from captures",
    ),
    # Nested groups: outer then inner, left to right.
    RegexFindTest(
        "captures_nested_groups",
        input="abc",
        regex="((a)(b))c",
        expected={"match": "abc", "idx": 0, "captures": ["ab", "a", "b"]},
        msg="$regexFind should capture nested groups outer then inner",
    ),
    # Named group included in captures without name.
    RegexFindTest(
        "captures_named_groups",
        input="abc123",
        regex="(?P<word>[a-z]+)(?P<num>[0-9]+)",
        expected={"match": "abc123", "idx": 0, "captures": ["abc", "123"]},
        msg="$regexFind should include named groups in captures array",
    ),
    # Empty capture group captures empty string.
    RegexFindTest(
        "captures_empty_group",
        input="abc",
        regex="()abc",
        expected={"match": "abc", "idx": 0, "captures": [""]},
        msg="$regexFind should capture empty string for empty group",
    ),
    # Lookahead with capture.
    RegexFindTest(
        "captures_lookahead",
        input="foobar",
        regex="foo(?=(bar))",
        expected={"match": "foo", "idx": 0, "captures": ["bar"]},
        msg="$regexFind should capture inside lookahead",
    ),
]

# Property [Encoding]: multi-byte UTF-8 characters in the match itself are preserved correctly.
REGEXFIND_ENCODING_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "encoding_2byte_in_match",
        input="caf\u00e9",
        regex="\u00e9",
        expected={"match": "\u00e9", "idx": 3, "captures": []},
        msg="$regexFind should match 2-byte UTF-8 character",
    ),
    RegexFindTest(
        "encoding_3byte_in_match",
        input="hello日world",
        regex="日",
        expected={"match": "日", "idx": 5, "captures": []},
        msg="$regexFind should match 3-byte UTF-8 character",
    ),
    RegexFindTest(
        "encoding_4byte_in_match",
        input="hello🎉world",
        regex="🎉",
        expected={"match": "🎉", "idx": 5, "captures": []},
        msg="$regexFind should match 4-byte UTF-8 emoji",
    ),
    RegexFindTest(
        "encoding_multibyte_span",
        input="日本語",
        regex="本語",
        expected={"match": "本語", "idx": 1, "captures": []},
        msg="$regexFind should match span of multi-byte characters",
    ),
    RegexFindTest(
        "encoding_combining_mark_in_match",
        input="e\u0301",
        regex="e\u0301",
        expected={"match": "e\u0301", "idx": 0, "captures": []},
        msg="$regexFind should preserve combining mark in match",
    ),
    RegexFindTest(
        "encoding_precomposed_not_decomposed",
        input="\u00e9",
        regex="e\u0301",
        expected=None,
        msg="$regexFind should not normalize precomposed to decomposed",
    ),
    RegexFindTest(
        "encoding_s_no_nbsp",
        input="\u00a0hello",
        regex="\\s",
        expected=None,
        msg="$regexFind \\s should not match NBSP",
    ),
]

# Property [Edge Cases]: empty strings, large inputs, and control characters are handled
# correctly.
REGEXFIND_EDGE_TESTS: list[RegexFindTest] = [
    RegexFindTest(
        "edge_empty_input_empty_regex",
        input="",
        regex="",
        expected={"match": "", "idx": 0, "captures": []},
        msg="$regexFind should match empty regex on empty input at idx 0",
    ),
    RegexFindTest(
        "edge_nonempty_input_empty_regex",
        input="hello",
        regex="",
        expected={"match": "", "idx": 0, "captures": []},
        msg="$regexFind empty regex should match at idx 0 of non-empty input",
    ),
    RegexFindTest(
        "edge_empty_input_nonempty_regex",
        input="",
        regex="abc",
        expected=None,
        msg="$regexFind should return null for no match on empty input",
    ),
    RegexFindTest(
        "edge_newline",
        input="hello\nworld",
        regex="world",
        expected={"match": "world", "idx": 6, "captures": []},
        msg="$regexFind should match across newline in input",
    ),
    RegexFindTest(
        "edge_tab",
        input="hello\tworld",
        regex="world",
        expected={"match": "world", "idx": 6, "captures": []},
        msg="$regexFind should match across tab in input",
    ),
    RegexFindTest(
        "edge_null_byte",
        input="hello\x00world",
        regex="world",
        expected={"match": "world", "idx": 6, "captures": []},
        msg="$regexFind should match across null byte in input",
    ),
    RegexFindTest(
        "edge_carriage_return",
        input="hello\rworld",
        regex="world",
        expected={"match": "world", "idx": 6, "captures": []},
        msg="$regexFind should match across carriage return in input",
    ),
]

REGEXFIND_MATCHING_ALL_TESTS = (
    REGEXFIND_FIRST_MATCH_TESTS
    + REGEXFIND_IDX_CODEPOINT_TESTS
    + REGEXFIND_CAPTURES_TESTS
    + REGEXFIND_ENCODING_TESTS
    + REGEXFIND_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REGEXFIND_MATCHING_ALL_TESTS))
def test_regexfind_cases(collection, test_case: RegexFindTest):
    """Test $regexFind matching behavior cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
