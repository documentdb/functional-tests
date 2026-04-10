from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [Encoding]: multi-byte UTF-8 characters, combining marks, zero-width characters, and
# special code points are each counted as one code point.
SUBSTRCP_ENCODING_TESTS: list[SubstrCPTest] = [
    # U+00E9 é is 2 bytes in UTF-8 but one code point.
    SubstrCPTest(
        "encoding_2byte",
        string="café",
        index=3,
        count=1,
        expected="é",
        msg="$substrCP should count 2-byte UTF-8 character as one code point",
    ),
    # CJK characters are 3 bytes in UTF-8.
    SubstrCPTest(
        "encoding_3byte",
        string="日本語",
        index=1,
        count=1,
        expected="本",
        msg="$substrCP should count 3-byte CJK character as one code point",
    ),
    # Emoji are 4 bytes in UTF-8.
    SubstrCPTest(
        "encoding_4byte",
        string="🎉🚀✨",
        index=1,
        count=1,
        expected="🚀",
        msg="$substrCP should count 4-byte emoji as one code point",
    ),
    # Precomposed U+00E9 is a single code point, unlike decomposed e + U+0301.
    SubstrCPTest(
        "encoding_precomposed",
        string="\u00e9X",
        index=0,
        count=1,
        expected="\u00e9",
        msg="$substrCP should treat precomposed character as one code point",
    ),
    # U+FEFF BOM is one code point.
    SubstrCPTest(
        "encoding_bom",
        string="\ufeffhello",
        index=0,
        count=1,
        expected="\ufeff",
        msg="$substrCP should count BOM as one code point",
    ),
    # Embedded null byte U+0000 is one code point.
    SubstrCPTest(
        "encoding_null_byte",
        string="a\x00b",
        index=1,
        count=1,
        expected="\x00",
        msg="$substrCP should count embedded null byte as one code point",
    ),
    # Mixed whitespace: space, tab, newline, carriage return, space.
    SubstrCPTest(
        "encoding_whitespace_mix",
        string=" \t\n\r ",
        index=2,
        count=1,
        expected="\n",
        msg="$substrCP should correctly index across different whitespace characters",
    ),
    # Control character U+0001.
    SubstrCPTest(
        "encoding_control_char",
        string="\x01\x1f",
        index=0,
        count=1,
        expected="\x01",
        msg="$substrCP should count control characters as one code point each",
    ),
    # U+200B Zero-Width Space is one code point.
    SubstrCPTest(
        "encoding_zwsp",
        string="a\u200bb",
        index=1,
        count=1,
        expected="\u200b",
        msg="$substrCP should count ZWSP as one code point",
    ),
    # U+200F Right-to-Left Mark is one code point.
    SubstrCPTest(
        "encoding_rtl_mark",
        string="a\u200fb",
        index=1,
        count=1,
        expected="\u200f",
        msg="$substrCP should count directional mark as one code point",
    ),
    # U+00A0 NBSP, U+2002 en space, U+2003 em space are each one code point.
    SubstrCPTest(
        "encoding_nbsp",
        string="\u00a0X",
        index=0,
        count=1,
        expected="\u00a0",
        msg="$substrCP should count NBSP as one code point",
    ),
    SubstrCPTest(
        "encoding_en_em_space",
        string="\u2002\u2003",
        index=1,
        count=1,
        expected="\u2003",
        msg="$substrCP should count en/em space as one code point each",
    ),
    # U+D7FF (last code point before surrogate range).
    SubstrCPTest(
        "encoding_boundary_d7ff",
        string="\ud7ff",
        index=0,
        count=1,
        expected="\ud7ff",
        msg="$substrCP should handle U+D7FF correctly",
    ),
    # U+E000 (first private use area character).
    SubstrCPTest(
        "encoding_boundary_e000",
        string="\ue000",
        index=0,
        count=1,
        expected="\ue000",
        msg="$substrCP should handle U+E000 correctly",
    ),
    # U+FFFF (last BMP character).
    SubstrCPTest(
        "encoding_boundary_ffff",
        string="\uffff",
        index=0,
        count=1,
        expected="\uffff",
        msg="$substrCP should handle U+FFFF correctly",
    ),
    # U+10000 (first supplementary plane character).
    SubstrCPTest(
        "encoding_boundary_10000",
        string="\U00010000",
        index=0,
        count=1,
        expected="\U00010000",
        msg="$substrCP should handle U+10000 correctly",
    ),
    # U+10FFFF (last valid Unicode code point).
    SubstrCPTest(
        "encoding_boundary_10ffff",
        string="\U0010ffff",
        index=0,
        count=1,
        expected="\U0010ffff",
        msg="$substrCP should handle U+10FFFF correctly",
    ),
    SubstrCPTest(
        "encoding_json_chars",
        string='{"key": [1]}',
        index=0,
        count=5,
        expected='{"key',
        msg="$substrCP should treat JSON/BSON special characters as regular characters",
    ),
    SubstrCPTest(
        "encoding_backslash",
        string="a\\b\\c",
        index=1,
        count=3,
        expected="\\b\\",
        msg="$substrCP should treat backslash as a regular character",
    ),
]

# Property [Grapheme Splitting]: the operator splits at code point boundaries, not grapheme cluster
# boundaries, so combining marks and ZWJ emoji components are extracted independently.
SUBSTRCP_GRAPHEME_SPLIT_TESTS: list[SubstrCPTest] = [
    # Decomposed e + U+0301 combining acute accent = 2 code points.
    SubstrCPTest(
        "grapheme_base_without_combining",
        string="e\u0301",
        index=0,
        count=1,
        expected="e",
        msg="$substrCP should extract base character without combining mark",
    ),
    SubstrCPTest(
        "grapheme_combining_mark_alone",
        string="e\u0301",
        index=1,
        count=1,
        expected="\u0301",
        msg="$substrCP should extract combining mark alone",
    ),
    # ZWJ family emoji: 👨 + ZWJ + 👩 + ZWJ + 👧 + ZWJ + 👦 = 7 code points.
    SubstrCPTest(
        "grapheme_zwj_emoji_first",
        string="👨\u200d👩\u200d👧\u200d👦",
        index=0,
        count=1,
        expected="👨",
        msg="$substrCP should extract first emoji from ZWJ sequence",
    ),
    SubstrCPTest(
        "grapheme_zwj_emoji_joiner",
        string="👨\u200d👩\u200d👧\u200d👦",
        index=1,
        count=1,
        expected="\u200d",
        msg="$substrCP should extract ZWJ joiner from emoji sequence",
    ),
    SubstrCPTest(
        "grapheme_zwj_emoji_partial",
        string="👨\u200d👩\u200d👧\u200d👦",
        index=0,
        count=3,
        expected="👨\u200d👩",
        msg="$substrCP should split ZWJ emoji sequence at code point boundaries",
    ),
]


SUBSTRCP_ENCODING_ALL_TESTS = SUBSTRCP_ENCODING_TESTS + SUBSTRCP_GRAPHEME_SPLIT_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_ENCODING_ALL_TESTS))
def test_substrcp_encoding(collection, test_case: SubstrCPTest):
    """Test $substrCP encoding and grapheme splitting cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
