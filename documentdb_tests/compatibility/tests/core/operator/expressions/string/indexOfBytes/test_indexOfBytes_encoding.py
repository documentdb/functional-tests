from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.indexOfBytes_common import (
    IndexOfBytesTest,
)

# Property [Encoding]: the operator matches and indexes by raw UTF-8 byte sequences without
# Unicode normalization, and the result is a byte index rather than a codepoint index.
INDEXOFBYTES_ENCODING_TESTS: list[IndexOfBytesTest] = [
    # Character after 2-byte é (U+00E9): byte index 2, codepoint index 1.
    IndexOfBytesTest(
        "encoding_after_2byte",
        args=["éa", "a"],
        expected=2,
        msg="$indexOfBytes should return byte index 2 after 2-byte character",
    ),
    # Character after 3-byte 日 (U+65E5): byte index 3, codepoint index 1.
    IndexOfBytesTest(
        "encoding_after_3byte",
        args=["日a", "a"],
        expected=3,
        msg="$indexOfBytes should return byte index 3 after 3-byte character",
    ),
    # Character after 4-byte 🎉 (U+1F389): byte index 4, codepoint index 1.
    IndexOfBytesTest(
        "encoding_after_4byte",
        args=["🎉a", "a"],
        expected=4,
        msg="$indexOfBytes should return byte index 4 after 4-byte character",
    ),
    IndexOfBytesTest(
        "encoding_find_multibyte_substr",
        args=["café", "é"],
        expected=3,
        msg="$indexOfBytes should find 2-byte substring at correct byte offset",
    ),
    # Decomposed é ("e" U+0065 + combining acute U+0301) found in a decomposed string.
    IndexOfBytesTest(
        "encoding_find_decomposed_in_decomposed",
        args=["cafe\u0301", "e\u0301"],
        expected=3,
        msg="$indexOfBytes should find decomposed sequence in decomposed string",
    ),
    # ASCII "e" does not match precomposed é (U+00E9).
    IndexOfBytesTest(
        "encoding_ascii_vs_precomposed",
        args=["café", "e"],
        expected=-1,
        msg="$indexOfBytes should not match ASCII 'e' against precomposed é",
    ),
    # Decomposed é is "e" (U+0065) + combining acute (U+0301). "e" matches the e byte.
    IndexOfBytesTest(
        "encoding_ascii_in_decomposed",
        args=["cafe\u0301", "e"],
        expected=3,
        msg="$indexOfBytes should find ASCII 'e' in decomposed é sequence",
    ),
    # Precomposed é (U+00E9) and decomposed e + combining acute (U+0301) are distinct byte
    # sequences.
    IndexOfBytesTest(
        "encoding_precomposed_in_decomposed",
        args=["cafe\u0301", "\u00e9"],
        expected=-1,
        msg="$indexOfBytes should not find precomposed é in decomposed string",
    ),
    IndexOfBytesTest(
        "encoding_decomposed_in_precomposed",
        args=["caf\u00e9", "e\u0301"],
        expected=-1,
        msg="$indexOfBytes should not find decomposed é in precomposed string",
    ),
    # start=1 falls in the middle of 2-byte é; partial bytes are skipped, "a" found at byte 2.
    IndexOfBytesTest(
        "encoding_start_mid_2byte",
        args=["éab", "a", 1],
        expected=2,
        msg="$indexOfBytes should skip partial 2-byte char when start is mid-character",
    ),
    # start=1 falls in the middle of 3-byte 日; "a" found at byte 3.
    IndexOfBytesTest(
        "encoding_start_mid_3byte",
        args=["日a", "a", 1],
        expected=3,
        msg="$indexOfBytes should skip partial 3-byte char when start is mid-character",
    ),
    # start=1 falls in the middle of 4-byte 🎉; "a" found at byte 4.
    IndexOfBytesTest(
        "encoding_start_mid_4byte",
        args=["🎉a", "a", 1],
        expected=4,
        msg="$indexOfBytes should skip partial 4-byte char when start is mid-character",
    ),
    # é spans bytes 1-2, but end=2 excludes byte 2 so the match is partial.
    IndexOfBytesTest(
        "encoding_end_mid_2byte",
        args=["aé", "é", 0, 2],
        expected=-1,
        msg="$indexOfBytes should return -1 when end splits a 2-byte character",
    ),
    # 日 spans bytes 1-3, but end=2 splits it.
    IndexOfBytesTest(
        "encoding_end_mid_3byte",
        args=["a日", "日", 0, 2],
        expected=-1,
        msg="$indexOfBytes should return -1 when end splits a 3-byte character",
    ),
    # 🎉 spans bytes 1-4, but end=2 splits it.
    IndexOfBytesTest(
        "encoding_end_mid_4byte",
        args=["a🎉", "🎉", 0, 2],
        expected=-1,
        msg="$indexOfBytes should return -1 when end splits a 4-byte character",
    ),
    # Start and end parameters are byte offsets; 寿司 is two 3-byte characters (6 bytes total).
    IndexOfBytesTest(
        "encoding_multibyte_start",
        args=["寿司", "司", 3],
        expected=3,
        msg="$indexOfBytes should find 3-byte char at byte offset with start",
    ),
    IndexOfBytesTest(
        "encoding_multibyte_start_end_excludes",
        args=["寿司", "司", 3, 3],
        expected=-1,
        msg="$indexOfBytes should return -1 when end excludes match in multi-byte string",
    ),
    IndexOfBytesTest(
        "encoding_multibyte_start_end_includes",
        args=["寿司", "司", 3, 6],
        expected=3,
        msg="$indexOfBytes should find match when end includes it in multi-byte string",
    ),
    IndexOfBytesTest(
        "encoding_multibyte_start_past_match",
        args=["寿司", "司", 6],
        expected=-1,
        msg="$indexOfBytes should return -1 when start is past match in multi-byte string",
    ),
    # Null bytes are single-byte characters and do not terminate the string.
    IndexOfBytesTest(
        "encoding_null_byte_found",
        args=["a\x00b", "\x00"],
        expected=1,
        msg="$indexOfBytes should find embedded null byte",
    ),
    IndexOfBytesTest(
        "encoding_after_null_byte",
        args=["a\x00b", "b"],
        expected=2,
        msg="$indexOfBytes should find character after embedded null byte",
    ),
    IndexOfBytesTest(
        "encoding_null_byte_with_start",
        args=["a\x00a\x00", "\x00", 2],
        expected=3,
        msg="$indexOfBytes should find second null byte when start skips first",
    ),
    IndexOfBytesTest(
        "encoding_null_byte_with_start_end",
        args=["\x00a\x00ab", "\x00", 2, 3],
        expected=2,
        msg="$indexOfBytes should find null byte within start/end range",
    ),
    # Control characters U+0001 and U+001F are single-byte and findable.
    IndexOfBytesTest(
        "encoding_control_soh",
        args=["a\x01b", "\x01"],
        expected=1,
        msg="$indexOfBytes should find SOH control character",
    ),
    IndexOfBytesTest(
        "encoding_control_us",
        args=["a\x1fb", "\x1f"],
        expected=1,
        msg="$indexOfBytes should find US control character",
    ),
    # Whitespace characters are findable as substrings.
    IndexOfBytesTest(
        "encoding_tab",
        args=["a\tb", "\t"],
        expected=1,
        msg="$indexOfBytes should find tab character",
    ),
    IndexOfBytesTest(
        "encoding_newline",
        args=["a\nb", "\n"],
        expected=1,
        msg="$indexOfBytes should find newline character",
    ),
    IndexOfBytesTest(
        "encoding_cr",
        args=["a\rb", "\r"],
        expected=1,
        msg="$indexOfBytes should find carriage return character",
    ),
    # U+00A0 non-breaking space (2 bytes) is distinct from ASCII space.
    IndexOfBytesTest(
        "encoding_nbsp_found",
        args=["a\u00a0b", "\u00a0"],
        expected=1,
        msg="$indexOfBytes should find non-breaking space",
    ),
    IndexOfBytesTest(
        "encoding_nbsp_vs_space",
        args=["a\u00a0b", " "],
        expected=-1,
        msg="$indexOfBytes should not match ASCII space against NBSP",
    ),
    IndexOfBytesTest(
        "encoding_space_vs_nbsp",
        args=["a b", "\u00a0"],
        expected=-1,
        msg="$indexOfBytes should not match NBSP against ASCII space",
    ),
    # U+2000 en space (3 bytes) is distinct from ASCII space.
    IndexOfBytesTest(
        "encoding_en_space_found",
        args=["a\u2000b", "\u2000"],
        expected=1,
        msg="$indexOfBytes should find en space",
    ),
    IndexOfBytesTest(
        "encoding_en_space_vs_space",
        args=["a\u2000b", " "],
        expected=-1,
        msg="$indexOfBytes should not match ASCII space against en space",
    ),
    # Zero-width characters are findable at their byte offsets.
    # U+FEFF BOM (3 bytes) at byte 5 in "hello\ufeff".
    IndexOfBytesTest(
        "encoding_bom_found",
        args=["hello\ufeff", "\ufeff"],
        expected=5,
        msg="$indexOfBytes should find BOM at correct byte offset",
    ),
    # U+200B ZWSP (3 bytes) at byte 1 in "a\u200b".
    IndexOfBytesTest(
        "encoding_zwsp_found",
        args=["a\u200b", "\u200b"],
        expected=1,
        msg="$indexOfBytes should find zero-width space",
    ),
    # U+0301 combining acute (2 bytes) is findable within a combining sequence at byte 4.
    IndexOfBytesTest(
        "encoding_combining_mark_alone",
        args=["cafe\u0301", "\u0301"],
        expected=4,
        msg="$indexOfBytes should find combining mark alone at byte offset",
    ),
    # é (U+00E9, UTF-8: C3 A9) and Ã (U+00C3, UTF-8: C3 83) share leading UTF-8 byte 0xC3 but
    # are not cross-matched.
    IndexOfBytesTest(
        "encoding_no_leading_byte_cross",
        args=["\u00e9", "\u00c3"],
        expected=-1,
        msg="$indexOfBytes should not cross-match chars sharing a leading UTF-8 byte",
    ),
    IndexOfBytesTest(
        "encoding_no_leading_byte_cross_rev",
        args=["\u00c3", "\u00e9"],
        expected=-1,
        msg="$indexOfBytes should not cross-match chars sharing a leading UTF-8 byte (reversed)",
    ),
]

# Property [Case Sensitivity]: search is strictly case-sensitive with no Unicode case folding,
# ligature expansion, or locale-dependent mapping.
INDEXOFBYTES_CASE_SENSITIVITY_TESTS: list[IndexOfBytesTest] = [
    # ASCII case differences.
    IndexOfBytesTest(
        "case_ascii_upper_in_lower",
        args=["hello", "E"],
        expected=-1,
        msg="$indexOfBytes should not find uppercase in lowercase ASCII",
    ),
    IndexOfBytesTest(
        "case_ascii_lower_in_upper",
        args=["HELLO", "e"],
        expected=-1,
        msg="$indexOfBytes should not find lowercase in uppercase ASCII",
    ),
    # Greek sigma: uppercase U+03A3 vs lowercase U+03C3.
    IndexOfBytesTest(
        "case_greek_upper_sigma",
        args=["σ", "Σ"],
        expected=-1,
        msg="$indexOfBytes should not case-fold Greek sigma",
    ),
    IndexOfBytesTest(
        "case_greek_lower_sigma",
        args=["Σ", "σ"],
        expected=-1,
        msg="$indexOfBytes should not case-fold Greek uppercase sigma",
    ),
    # Cyrillic: uppercase U+0414 vs lowercase U+0434.
    IndexOfBytesTest(
        "case_cyrillic_upper_de",
        args=["д", "Д"],
        expected=-1,
        msg="$indexOfBytes should not case-fold Cyrillic de",
    ),
    IndexOfBytesTest(
        "case_cyrillic_lower_de",
        args=["Д", "д"],
        expected=-1,
        msg="$indexOfBytes should not case-fold Cyrillic uppercase de",
    ),
    # No sharp-s expansion: U+00DF does not match "SS" or "ss".
    IndexOfBytesTest(
        "case_sharp_s_vs_upper_ss",
        args=["ß", "SS"],
        expected=-1,
        msg="$indexOfBytes should not expand sharp-s to SS",
    ),
    IndexOfBytesTest(
        "case_sharp_s_vs_lower_ss",
        args=["ß", "ss"],
        expected=-1,
        msg="$indexOfBytes should not expand sharp-s to ss",
    ),
    # No ligature expansion: U+FB01 does not match "fi".
    IndexOfBytesTest(
        "case_ligature_fi",
        args=["\ufb01", "fi"],
        expected=-1,
        msg="$indexOfBytes should not expand fi ligature",
    ),
    # No locale-dependent mapping: U+0131 (dotless i) does not match "i".
    IndexOfBytesTest(
        "case_dotless_i",
        args=["\u0131", "i"],
        expected=-1,
        msg="$indexOfBytes should not map dotless i to ASCII i",
    ),
]


INDEXOFBYTES_ENCODING_ALL_TESTS = INDEXOFBYTES_ENCODING_TESTS + INDEXOFBYTES_CASE_SENSITIVITY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFBYTES_ENCODING_ALL_TESTS))
def test_indexofbytes_cases(collection, test_case: IndexOfBytesTest):
    """Test $indexOfBytes cases."""
    result = execute_expression(collection, {"$indexOfBytes": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
