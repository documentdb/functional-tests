from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)

# Property [idx Code Point Semantics]: idx counts Unicode code points, not bytes. Each character
# contributes 1 regardless of UTF-8 byte width.
REGEXFINDALL_IDX_CODEPOINT_TESTS: list[RegexFindAllTest] = [
    # U+00E9 is 2 bytes. Byte index would be 2, codepoint index is 1.
    RegexFindAllTest(
        "idx_cp_2byte_prefix",
        input="\u00e9abc",
        regex="abc",
        expected=[{"match": "abc", "idx": 1, "captures": []}],
        msg="$regexFindAll idx should count 2-byte character as one code point",
    ),
    # U+65E5 is 3 bytes. Byte index would be 3, codepoint index is 1.
    RegexFindAllTest(
        "idx_cp_3byte_prefix",
        input="日abc",
        regex="abc",
        expected=[{"match": "abc", "idx": 1, "captures": []}],
        msg="$regexFindAll idx should count 3-byte CJK character as one code point",
    ),
    # U+1F389 is 4 bytes. Byte index would be 4, codepoint index is 1.
    RegexFindAllTest(
        "idx_cp_4byte_prefix",
        input="🎉abc",
        regex="abc",
        expected=[{"match": "abc", "idx": 1, "captures": []}],
        msg="$regexFindAll idx should count 4-byte emoji as one code point",
    ),
    # Mix of 2-byte, 3-byte, and 4-byte chars. Byte index would be 9, codepoint index is 3.
    RegexFindAllTest(
        "idx_cp_mixed_byte_widths",
        input="\u00e9日🎉abc",
        regex="abc",
        expected=[{"match": "abc", "idx": 3, "captures": []}],
        msg="$regexFindAll idx should count mixed 2/3/4-byte characters as one code point each",
    ),
    # Three 3-byte CJK chars. Byte index would be 9, codepoint index is 3.
    RegexFindAllTest(
        "idx_cp_cjk_prefix",
        input="日本語abc",
        regex="abc",
        expected=[{"match": "abc", "idx": 3, "captures": []}],
        msg="$regexFindAll idx should count three CJK characters as three code points",
    ),
    # Combining mark (e + U+0301) is two codepoints, not one. idx would be 1 if normalized to
    # precomposed U+00E9.
    RegexFindAllTest(
        "idx_cp_combining_mark",
        input="e\u0301abc",
        regex="abc",
        expected=[{"match": "abc", "idx": 2, "captures": []}],
        msg="$regexFindAll idx should count combining mark as a separate code point",
    ),
]


# Property [Encoding]: multi-byte UTF-8 characters in the match itself are preserved correctly.
REGEXFINDALL_ENCODING_TESTS: list[RegexFindAllTest] = [
    # 2-byte character in match (U+00E9).
    RegexFindAllTest(
        "encoding_2byte_in_match",
        input="caf\u00e9",
        regex="\u00e9",
        expected=[{"match": "\u00e9", "idx": 3, "captures": []}],
        msg="$regexFindAll should preserve 2-byte character in match output",
    ),
    # 3-byte character in match (U+65E5).
    RegexFindAllTest(
        "encoding_3byte_in_match",
        input="hello日world",
        regex="日",
        expected=[{"match": "日", "idx": 5, "captures": []}],
        msg="$regexFindAll should preserve 3-byte CJK character in match output",
    ),
    # 4-byte emoji in match (U+1F389).
    RegexFindAllTest(
        "encoding_4byte_in_match",
        input="hello🎉world",
        regex="🎉",
        expected=[{"match": "🎉", "idx": 5, "captures": []}],
        msg="$regexFindAll should preserve 4-byte emoji in match output",
    ),
    # Match spanning multiple multi-byte characters.
    RegexFindAllTest(
        "encoding_multibyte_span",
        input="日本語",
        regex="本語",
        expected=[{"match": "本語", "idx": 1, "captures": []}],
        msg="$regexFindAll should match span of multiple multi-byte characters",
    ),
    # Combining mark (U+0301) in the match value is preserved.
    RegexFindAllTest(
        "encoding_combining_mark_in_match",
        input="e\u0301",
        regex="e\u0301",
        expected=[{"match": "e\u0301", "idx": 0, "captures": []}],
        msg="$regexFindAll should preserve combining mark in match output",
    ),
    # Precomposed U+00E9 and decomposed e+U+0301 are not normalized to each other.
    RegexFindAllTest(
        "encoding_precomposed_not_decomposed",
        input="\u00e9",
        regex="e\u0301",
        expected=[],
        msg="$regexFindAll should not match precomposed character with decomposed regex",
    ),
    # \s does NOT match NBSP (U+00A0).
    RegexFindAllTest(
        "encoding_s_no_nbsp",
        input="\u00a0hello",
        regex="\\s",
        expected=[],
        msg="$regexFindAll \\s should not match non-breaking space U+00A0",
    ),
    # Multi-byte characters between matches. Each contributes 1 to idx
    # regardless of byte width.
    RegexFindAllTest(
        "encoding_multibyte_between_matches",
        input="x日x🎉x",
        regex="x",
        expected=[
            {"match": "x", "idx": 0, "captures": []},
            {"match": "x", "idx": 2, "captures": []},
            {"match": "x", "idx": 4, "captures": []},
        ],
        msg="$regexFindAll should count multi-byte chars between matches as one code point each",
    ),
]

REGEXFINDALL_ENCODING_ALL_TESTS = REGEXFINDALL_IDX_CODEPOINT_TESTS + REGEXFINDALL_ENCODING_TESTS


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_ENCODING_ALL_TESTS))
def test_regexfindall_encoding(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll Unicode encoding and idx code point semantics."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
