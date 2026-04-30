from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.indexOfCP_common import (
    IndexOfCPTest,
)

# Property [Code Point Indexing]: the result is a UTF-8 code point index, not a byte index.
INDEXOFCP_CODEPOINT_TESTS: list[IndexOfCPTest] = [
    # Character after 2-byte é (U+00E9): code point index 1 (byte index would be 2).
    IndexOfCPTest(
        "cp_after_2byte",
        args=["éa", "a"],
        expected=1,
        msg="$indexOfCP should return cp index 1 after 2-byte character",
    ),
    # Character after 3-byte 日 (U+65E5): code point index 1 (byte index would be 3).
    IndexOfCPTest(
        "cp_after_3byte",
        args=["日a", "a"],
        expected=1,
        msg="$indexOfCP should return cp index 1 after 3-byte character",
    ),
    # Character after 4-byte 🎉 (U+1F389): code point index 1 (byte index would be 4).
    IndexOfCPTest(
        "cp_after_4byte",
        args=["🎉a", "a"],
        expected=1,
        msg="$indexOfCP should return cp index 1 after 4-byte character",
    ),
    # Finding a multi-byte substring returns its code point index, not byte index.
    IndexOfCPTest(
        "cp_find_multibyte_substr",
        args=["café", "é"],
        expected=3,
        msg="$indexOfCP should find multi-byte substring at code point index",
    ),
    # Decomposed é ("e" U+0065 + combining acute U+0301) found in a decomposed string.
    IndexOfCPTest(
        "cp_find_decomposed_in_decomposed",
        args=["cafe\u0301", "e\u0301"],
        expected=3,
        msg="$indexOfCP should find decomposed sequence in decomposed string",
    ),
    # ASCII "e" does not match precomposed é (U+00E9).
    IndexOfCPTest(
        "cp_ascii_vs_precomposed",
        args=["café", "e"],
        expected=-1,
        msg="$indexOfCP should not match ASCII 'e' against precomposed é",
    ),
    # Decomposed é is "e" (U+0065) + combining acute (U+0301). "e" matches at code point 3.
    IndexOfCPTest(
        "cp_ascii_in_decomposed",
        args=["cafe\u0301", "e"],
        expected=3,
        msg="$indexOfCP should find ASCII 'e' in decomposed é sequence",
    ),
    # Precomposed é (U+00E9) and decomposed e + combining acute (U+0301) are distinct code point
    # sequences.
    IndexOfCPTest(
        "cp_precomposed_in_decomposed",
        args=["cafe\u0301", "\u00e9"],
        expected=-1,
        msg="$indexOfCP should not find precomposed é in decomposed string",
    ),
    IndexOfCPTest(
        "cp_decomposed_in_precomposed",
        args=["caf\u00e9", "e\u0301"],
        expected=-1,
        msg="$indexOfCP should not find decomposed é in precomposed string",
    ),
    # Start and end parameters are code point offsets, not byte offsets.
    IndexOfCPTest(
        "cp_multibyte_start",
        args=["寿司", "司", 1],
        expected=1,
        msg="$indexOfCP should find 3-byte char at cp offset with start",
    ),
    IndexOfCPTest(
        "cp_multibyte_start_end_excludes",
        args=["寿司", "司", 1, 1],
        expected=-1,
        msg="$indexOfCP should return -1 when end excludes match in multi-byte string",
    ),
    IndexOfCPTest(
        "cp_multibyte_start_end_includes",
        args=["寿司", "司", 1, 2],
        expected=1,
        msg="$indexOfCP should find match when end includes it in multi-byte string",
    ),
    IndexOfCPTest(
        "cp_multibyte_start_past_match",
        args=["寿司", "司", 2],
        expected=-1,
        msg="$indexOfCP should return -1 when start is past match in multi-byte string",
    ),
    # Null bytes are single code points and do not terminate the string.
    IndexOfCPTest(
        "cp_null_byte_found",
        args=["a\x00b", "\x00"],
        expected=1,
        msg="$indexOfCP should find embedded null byte",
    ),
    IndexOfCPTest(
        "cp_after_null_byte",
        args=["a\x00b", "b"],
        expected=2,
        msg="$indexOfCP should find character after embedded null byte",
    ),
    IndexOfCPTest(
        "cp_null_byte_with_start",
        args=["a\x00a\x00", "\x00", 2],
        expected=3,
        msg="$indexOfCP should find second null byte when start skips first",
    ),
    IndexOfCPTest(
        "cp_null_byte_with_start_end",
        args=["\x00a\x00ab", "\x00", 2, 3],
        expected=2,
        msg="$indexOfCP should find null byte within start/end range",
    ),
]


# Property [Case Sensitivity]: search is strictly case-sensitive with no Unicode case folding or
# locale-dependent mapping.
INDEXOFCP_CASE_SENSITIVITY_TESTS: list[IndexOfCPTest] = [
    # ASCII case differences are not matched.
    IndexOfCPTest(
        "case_ascii_upper_in_lower",
        args=["hello", "E"],
        expected=-1,
        msg="$indexOfCP should not find uppercase in lowercase ASCII",
    ),
    IndexOfCPTest(
        "case_ascii_lower_in_upper",
        args=["HELLO", "e"],
        expected=-1,
        msg="$indexOfCP should not find lowercase in uppercase ASCII",
    ),
    # Greek sigma: uppercase Σ (U+03A3) vs lowercase σ (U+03C3).
    IndexOfCPTest(
        "case_greek_sigma_upper_in_lower",
        args=["σ", "Σ"],
        expected=-1,
        msg="$indexOfCP should not case-fold Greek sigma",
    ),
    IndexOfCPTest(
        "case_greek_sigma_lower_in_upper",
        args=["Σ", "σ"],
        expected=-1,
        msg="$indexOfCP should not case-fold Greek uppercase sigma",
    ),
    # Cyrillic: uppercase Д (U+0414) vs lowercase д (U+0434).
    IndexOfCPTest(
        "case_cyrillic_upper_in_lower",
        args=["д", "Д"],
        expected=-1,
        msg="$indexOfCP should not case-fold Cyrillic de",
    ),
    IndexOfCPTest(
        "case_cyrillic_lower_in_upper",
        args=["Д", "д"],
        expected=-1,
        msg="$indexOfCP should not case-fold Cyrillic uppercase de",
    ),
    # No sharp-s expansion: ß (U+00DF) does not match "SS" or "ss".
    IndexOfCPTest(
        "case_sharp_s_vs_upper_ss",
        args=["ß", "SS"],
        expected=-1,
        msg="$indexOfCP should not expand sharp-s to SS",
    ),
    IndexOfCPTest(
        "case_sharp_s_vs_lower_ss",
        args=["ß", "ss"],
        expected=-1,
        msg="$indexOfCP should not expand sharp-s to ss",
    ),
    # No ligature expansion: ﬁ (U+FB01) does not match "fi".
    IndexOfCPTest(
        "case_ligature_fi",
        args=["ﬁ", "fi"],
        expected=-1,
        msg="$indexOfCP should not expand fi ligature",
    ),
    # No locale-dependent mapping: ı (U+0131, Turkish dotless i) does not match "i".
    IndexOfCPTest(
        "case_turkish_dotless_i",
        args=["ı", "i"],
        expected=-1,
        msg="$indexOfCP should not map dotless i to ASCII i",
    ),
]


# Property [Encoding and Character Handling]: special Unicode characters including control
# characters, non-ASCII whitespace, and zero-width characters are individually findable at their
# code point offsets.
INDEXOFCP_ENCODING_TESTS: list[IndexOfCPTest] = [
    # Control characters are single code points.
    IndexOfCPTest(
        "enc_control_soh",
        args=["a\x01b", "\x01"],
        expected=1,
        msg="$indexOfCP should find SOH control character",
    ),
    IndexOfCPTest(
        "enc_control_us",
        args=["a\x1fb", "\x1f"],
        expected=1,
        msg="$indexOfCP should find US control character",
    ),
    IndexOfCPTest(
        "enc_newline",
        args=["line1\nline2", "\n"],
        expected=5,
        msg="$indexOfCP should find newline character",
    ),
    IndexOfCPTest(
        "enc_tab", args=["col1\tcol2", "\t"], expected=4, msg="$indexOfCP should find tab character"
    ),
    IndexOfCPTest(
        "enc_carriage_return",
        args=["line1\rline2", "\r"],
        expected=5,
        msg="$indexOfCP should find carriage return character",
    ),
    # Non-breaking space (U+00A0) is distinct from ASCII space.
    IndexOfCPTest(
        "enc_nbsp_found",
        args=["a\u00a0b", "\u00a0"],
        expected=1,
        msg="$indexOfCP should find non-breaking space",
    ),
    IndexOfCPTest(
        "enc_nbsp_not_ascii_space",
        args=["a\u00a0b", " "],
        expected=-1,
        msg="$indexOfCP should not match ASCII space against NBSP",
    ),
    # En space (U+2000) is distinct from ASCII space.
    IndexOfCPTest(
        "enc_en_space_found",
        args=["a\u2000b", "\u2000"],
        expected=1,
        msg="$indexOfCP should find en space",
    ),
    IndexOfCPTest(
        "enc_en_space_not_ascii_space",
        args=["a\u2000b", " "],
        expected=-1,
        msg="$indexOfCP should not match ASCII space against en space",
    ),
    # BOM (U+FEFF).
    IndexOfCPTest(
        "enc_bom_found",
        args=["a\ufeffb", "\ufeff"],
        expected=1,
        msg="$indexOfCP should find BOM character",
    ),
    # ZWSP (U+200B).
    IndexOfCPTest(
        "enc_zwsp_found",
        args=["a\u200bb", "\u200b"],
        expected=1,
        msg="$indexOfCP should find zero-width space",
    ),
    # Combining mark alone (U+0301) is findable within a combining sequence.
    IndexOfCPTest(
        "enc_combining_mark_alone",
        args=["cafe\u0301", "\u0301"],
        expected=4,
        msg="$indexOfCP should find combining mark alone at code point offset",
    ),
]

INDEXOFCP_ENCODING_AND_CASE_TESTS = (
    INDEXOFCP_CODEPOINT_TESTS + INDEXOFCP_CASE_SENSITIVITY_TESTS + INDEXOFCP_ENCODING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(INDEXOFCP_ENCODING_AND_CASE_TESTS))
def test_indexofcp_encoding(collection, test_case: IndexOfCPTest):
    """Test $indexOfCP encoding and case sensitivity."""
    result = execute_expression(collection, {"$indexOfCP": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
