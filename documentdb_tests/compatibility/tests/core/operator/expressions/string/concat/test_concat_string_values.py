from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params

from .utils.concat_common import (
    ConcatTest,
)

# Property [Identity]: "" is the identity element. concat(s, "") == concat("", s) == s.
CONCAT_IDENTITY_TESTS: list[ConcatTest] = [
    ConcatTest(
        "identity_empty_right",
        args=["hello", ""],
        expected="hello",
        msg="$concat should treat empty string as identity on the right",
    ),
    ConcatTest(
        "identity_empty_left",
        args=["", "hello"],
        expected="hello",
        msg="$concat should treat empty string as identity on the left",
    ),
    ConcatTest(
        "identity_empty_both_sides",
        args=["", "hello", ""],
        expected="hello",
        msg="$concat should treat empty strings as identity on both sides",
    ),
    ConcatTest(
        "identity_single_empty",
        args=[""],
        expected="",
        msg="$concat of a single empty string should return empty string",
    ),
    ConcatTest(
        "identity_two_empty",
        args=["", ""],
        expected="",
        msg="$concat of two empty strings should return empty string",
    ),
    ConcatTest(
        "identity_many_empty",
        args=["", "", ""],
        expected="",
        msg="$concat of many empty strings should return empty string",
    ),
    ConcatTest(
        "identity_empty_between_strings",
        args=["a", "", "b"],
        expected="ab",
        msg="$concat should ignore empty string between non-empty strings",
    ),
    ConcatTest(
        "identity_empty_interspersed",
        args=["", "a", "", "b", ""],
        expected="ab",
        msg="$concat should ignore interspersed empty strings",
    ),
]

# Property [Ordering]: argument order is preserved; $concat is not commutative.
CONCAT_ORDERING_TESTS: list[ConcatTest] = [
    ConcatTest(
        "ordering_three_words",
        args=["hello", " ", "world"],
        expected="hello world",
        msg="$concat should preserve argument order for three words",
    ),
    ConcatTest(
        "ordering_reversed",
        args=["world", " ", "hello"],
        expected="world hello",
        msg="$concat should preserve reversed argument order",
    ),
    ConcatTest(
        "ordering_ab", args=["a", "b"], expected="ab", msg="$concat should produce 'ab' not 'ba'"
    ),
    ConcatTest(
        "ordering_ba", args=["b", "a"], expected="ba", msg="$concat should produce 'ba' not 'ab'"
    ),
    ConcatTest(
        "ordering_digits",
        args=["1", "2", "3"],
        expected="123",
        msg="$concat should preserve digit order",
    ),
    ConcatTest(
        "ordering_digits_reversed",
        args=["3", "2", "1"],
        expected="321",
        msg="$concat should preserve reversed digit order",
    ),
]

# Property [Unicode Integrity]: concatenation preserves byte and codepoint integrity for multi-byte
# UTF-8 strings.
CONCAT_UNICODE_TESTS: list[ConcatTest] = [
    ConcatTest(
        "unicode_latin_accents",
        args=["café", " ", "naïve"],
        expected="café naïve",
        msg="$concat should preserve Latin accented characters",
    ),
    ConcatTest(
        "unicode_cjk",
        args=["日本", "語"],
        expected="日本語",
        msg="$concat should preserve CJK characters",
    ),
    ConcatTest(
        "unicode_emoji",
        args=["🎉", "🚀", "✨"],
        expected="🎉🚀✨",
        msg="$concat should preserve emoji characters",
    ),
    # ZWJ (Zero Width Joiner, U+200D) joins characters into single glyphs.
    # 👨‍👩‍👧‍👦 = man + ZWJ + woman + ZWJ + girl + ZWJ + boy (family emoji)
    # 👨‍💻 = man + ZWJ + laptop (man technologist emoji)
    ConcatTest(
        "unicode_zwj_emoji",
        args=["👨\u200d👩\u200d👧\u200d👦", "👨\u200d💻"],
        expected="👨\u200d👩\u200d👧\u200d👦👨\u200d💻",
        msg="$concat should preserve ZWJ emoji sequences",
    ),
    ConcatTest(
        "unicode_zwj_at_boundary",
        args=["👨\u200d", "💻"],
        expected="👨\u200d💻",
        msg="$concat should join ZWJ at string boundary",
    ),
    ConcatTest(
        "unicode_combining_chars",
        args=["e\u0301", "n\u0303o"],
        expected="e\u0301n\u0303o",
        msg="$concat should preserve combining characters without normalization",
    ),
    ConcatTest(
        "unicode_mixed_scripts",
        args=["hello", "世界", "🌍"],
        expected="hello世界🌍",
        msg="$concat should handle mixed scripts",
    ),
    ConcatTest(
        "unicode_greek",
        args=["α", "β", "γ"],
        expected="αβγ",
        msg="$concat should preserve Greek characters",
    ),
    ConcatTest(
        "unicode_arabic",
        args=["مرحبا", " ", "عالم"],
        expected="مرحبا عالم",
        msg="$concat should preserve Arabic characters",
    ),
    # Combining mark at start of second arg should not be normalized to precomposed form (é).
    ConcatTest(
        "unicode_combining_at_boundary",
        args=["e", "\u0301"],
        expected="e\u0301",
        msg="$concat should not normalize combining mark at string boundary",
    ),
    # Precomposed (é) and decomposed (e + combining mark) forms must both survive without
    # normalization.
    ConcatTest(
        "unicode_precomposed_and_decomposed",
        args=["\u00e9", "e\u0301"],
        expected="\u00e9e\u0301",
        msg="$concat should preserve both precomposed and decomposed forms",
    ),
    # BOM is sometimes stripped as it is a leading encoding signal. After concat it lands mid-string
    # and must survive.
    ConcatTest(
        "unicode_bom_in_middle",
        args=["hello", "\ufeffworld"],
        expected="hello\ufeffworld",
        msg="$concat should preserve BOM character in middle of result",
    ),
    # Directional markers between concatenated strings must be preserved.
    ConcatTest(
        "unicode_directional_markers",
        args=["hello\u200f", "\u200eworld"],
        expected="hello\u200f\u200eworld",
        msg="$concat should preserve directional markers at string boundaries",
    ),
]

# Property [Character Preservation]: zero-width spaces, control characters, dollar-prefixed
# literals, locale-sensitive letters, and non-Latin scripts are preserved without transformation.
CONCAT_CHAR_PRESERVATION_TESTS: list[ConcatTest] = [
    # U+200B zero-width space.
    ConcatTest(
        "char_pres_zero_width_space",
        args=["a\u200bb", "c"],
        expected="a\u200bbc",
        msg="$concat should preserve zero-width space",
    ),
    # Control characters U+0001 and U+001F.
    ConcatTest(
        "char_pres_control_soh",
        args=["\x01", "a"],
        expected="\x01a",
        msg="$concat should preserve SOH control character",
    ),
    ConcatTest(
        "char_pres_control_us",
        args=["a", "\x1f"],
        expected="a\x1f",
        msg="$concat should preserve US control character",
    ),
    # Dollar-prefixed string via $literal is preserved as text, not a field reference.
    ConcatTest(
        "char_pres_dollar_literal",
        args=[{"$literal": "$hello"}, " world"],
        expected="$hello world",
        msg="$concat should preserve dollar-prefixed string via $literal",
    ),
    # German sharp s, fi ligature (U+FB01), Turkish dotless i (U+0131).
    ConcatTest(
        "char_pres_locale_sensitive",
        args=["ß", "ﬁ", "ı"],
        expected="ßﬁı",
        msg="$concat should preserve locale-sensitive characters",
    ),
    # Cyrillic and Deseret script characters.
    ConcatTest(
        "char_pres_cyrillic",
        args=["д", "Д"],
        expected="дД",
        msg="$concat should preserve Cyrillic characters",
    ),
    # U+10400 Deseret capital long I, U+10428 Deseret small long I.
    ConcatTest(
        "char_pres_deseret",
        args=["𐐀", "𐐨"],
        expected="𐐀𐐨",
        msg="$concat should preserve Deseret script characters",
    ),
]

# Property [Whitespace Preservation]: whitespace characters including CR, CRLF, non-breaking space,
# and Unicode whitespace are preserved in concatenation.
CONCAT_WHITESPACE_TESTS: list[ConcatTest] = [
    ConcatTest(
        "whitespace_cr",
        args=["a\rb", "c"],
        expected="a\rbc",
        msg="$concat should preserve carriage return",
    ),
    ConcatTest(
        "whitespace_crlf",
        args=["a\r\nb", "c"],
        expected="a\r\nbc",
        msg="$concat should preserve CRLF",
    ),
    # U+00A0 non-breaking space.
    ConcatTest(
        "whitespace_nbsp",
        args=["a\u00a0b", "c"],
        expected="a\u00a0bc",
        msg="$concat should preserve non-breaking space",
    ),
    # U+2000 en space.
    ConcatTest(
        "whitespace_en_space",
        args=["a\u2000b", "c"],
        expected="a\u2000bc",
        msg="$concat should preserve en space",
    ),
    # U+2003 em space.
    ConcatTest(
        "whitespace_em_space",
        args=["a\u2003b", "c"],
        expected="a\u2003bc",
        msg="$concat should preserve em space",
    ),
    ConcatTest(
        "whitespace_mixed",
        args=[" \t\n\r ", "x"],
        expected=" \t\n\r x",
        msg="$concat should preserve mixed whitespace characters",
    ),
]

CONCAT_STRING_VALUES_TESTS = (
    CONCAT_IDENTITY_TESTS
    + CONCAT_ORDERING_TESTS
    + CONCAT_UNICODE_TESTS
    + CONCAT_CHAR_PRESERVATION_TESTS
    + CONCAT_WHITESPACE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_STRING_VALUES_TESTS))
def test_concat_string_values_cases(collection, test_case: ConcatTest):
    """Test $concat string value cases."""
    result = execute_expression(collection, {"$concat": test_case.args})
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
