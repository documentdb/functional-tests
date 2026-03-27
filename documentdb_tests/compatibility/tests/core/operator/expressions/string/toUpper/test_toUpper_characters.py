from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.toUpper.utils.toUpper_common import (
    ToUpperTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Core Conversion Behavior]: only ASCII lowercase letters are converted to uppercase;
# all other characters pass through unchanged.
TOUPPER_CORE_TESTS: list[ToUpperTest] = [
    # ASCII lowercase to uppercase.
    ToUpperTest(
        "core_ascii_lowercase",
        value="hello",
        expected="HELLO",
        msg="$toUpper should convert ASCII lowercase to uppercase",
    ),
    ToUpperTest(
        "core_all_lowercase",
        value="abcdefghijklmnopqrstuvwxyz",
        expected="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        msg="$toUpper should convert all ASCII lowercase letters",
    ),
    # ASCII uppercase unchanged.
    ToUpperTest(
        "core_ascii_uppercase",
        value="HELLO",
        expected="HELLO",
        msg="$toUpper should leave ASCII uppercase unchanged",
    ),
    ToUpperTest(
        "core_all_uppercase",
        value="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        expected="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        msg="$toUpper should leave all ASCII uppercase letters unchanged",
    ),
    # Mixed case.
    ToUpperTest(
        "core_mixed_case",
        value="HeLLo WoRLd",
        expected="HELLO WORLD",
        msg="$toUpper should convert mixed case to uppercase",
    ),
    # Digits unchanged.
    ToUpperTest(
        "core_digits",
        value="abc123xyz",
        expected="ABC123XYZ",
        msg="$toUpper should leave digits unchanged",
    ),
    # Punctuation unchanged.
    ToUpperTest(
        "core_punctuation",
        value="hello, world!",
        expected="HELLO, WORLD!",
        msg="$toUpper should leave punctuation unchanged",
    ),
    ToUpperTest(
        "core_punctuation_only",
        value="!@#$%",
        expected="!@#$%",
        msg="$toUpper should return punctuation-only string unchanged",
    ),
    # Whitespace unchanged.
    ToUpperTest(
        "core_whitespace_space",
        value="hello world",
        expected="HELLO WORLD",
        msg="$toUpper should preserve spaces",
    ),
    ToUpperTest(
        "core_whitespace_tab",
        value="hello\tworld",
        expected="HELLO\tWORLD",
        msg="$toUpper should preserve tabs",
    ),
    ToUpperTest(
        "core_whitespace_newline",
        value="hello\nworld",
        expected="HELLO\nWORLD",
        msg="$toUpper should preserve newlines",
    ),
    # Unicode whitespace unchanged (non-breaking space U+00A0, en space U+2002, em space U+2003).
    ToUpperTest(
        "core_unicode_nbsp",
        value="a\u00a0b",
        expected="A\u00a0B",
        msg="$toUpper should preserve non-breaking space",
    ),
    ToUpperTest(
        "core_unicode_en_space",
        value="a\u2002b",
        expected="A\u2002B",
        msg="$toUpper should preserve en space",
    ),
    ToUpperTest(
        "core_unicode_em_space",
        value="a\u2003b",
        expected="A\u2003B",
        msg="$toUpper should preserve em space",
    ),
    # Control characters unchanged (U+0000 null, U+001F unit separator).
    ToUpperTest(
        "core_control_null",
        value="a\x00b",
        expected="A\x00B",
        msg="$toUpper should preserve null byte",
    ),
    ToUpperTest(
        "core_control_unit_sep",
        value="a\x1fb",
        expected="A\x1fB",
        msg="$toUpper should preserve unit separator",
    ),
    # Non-ASCII Unicode letters not converted.
    ToUpperTest(
        "core_latin_extended",
        value="café",
        expected="CAFé",
        msg="$toUpper should not convert non-ASCII Latin characters",
    ),
    ToUpperTest(
        "core_latin_diaeresis",
        value="naïve",
        expected="NAïVE",
        msg="$toUpper should not convert non-ASCII diaeresis characters",
    ),
    ToUpperTest(
        "core_greek_lowercase",
        value="αβγ",
        expected="αβγ",
        msg="$toUpper should not convert Greek lowercase letters",
    ),
    ToUpperTest(
        "core_cyrillic_lowercase",
        value="привет",
        expected="привет",
        msg="$toUpper should not convert Cyrillic lowercase letters",
    ),
    # Greek final sigma (ς, U+03C2) not converted.
    ToUpperTest(
        "core_greek_final_sigma",
        value="ς",
        expected="ς",
        msg="$toUpper should not convert Greek final sigma",
    ),
    # Turkish dotless i (ı, U+0131) not converted.
    ToUpperTest(
        "core_turkish_dotless_i",
        value="ı",
        expected="ı",
        msg="$toUpper should not convert Turkish dotless i",
    ),
    # Titlecase characters not converted (ǲ U+01F2, ǳ U+01F3).
    ToUpperTest(
        "core_titlecase_dz", value="ǲ", expected="ǲ", msg="$toUpper should not convert titlecase dz"
    ),
    ToUpperTest(
        "core_titlecase_dz_lower",
        value="ǳ",
        expected="ǳ",
        msg="$toUpper should not convert lowercase dz digraph",
    ),
    # Cherokee lowercase not converted (Ꭰ U+13A0 is uppercase, ꭰ U+AB70 is lowercase).
    ToUpperTest(
        "core_cherokee_lowercase",
        value="ꭰ",
        expected="ꭰ",
        msg="$toUpper should not convert Cherokee lowercase",
    ),
    # Enclosed alphanumerics not converted (ⓐ U+24D0).
    ToUpperTest(
        "core_enclosed_alpha",
        value="ⓐ",
        expected="ⓐ",
        msg="$toUpper should not convert enclosed alphanumerics",
    ),
    # Fullwidth ASCII not converted (ａ U+FF41).
    ToUpperTest(
        "core_fullwidth_a",
        value="ａ",
        expected="ａ",
        msg="$toUpper should not convert fullwidth ASCII",
    ),
    # Roman numeral letter forms not converted (ⅰ U+2170).
    ToUpperTest(
        "core_roman_numeral",
        value="ⅰ",
        expected="ⅰ",
        msg="$toUpper should not convert Roman numeral letter forms",
    ),
    # CJK unchanged.
    ToUpperTest(
        "core_cjk",
        value="日本語",
        expected="日本語",
        msg="$toUpper should leave CJK characters unchanged",
    ),
    # Emoji unchanged.
    ToUpperTest(
        "core_emoji", value="🎉🚀", expected="🎉🚀", msg="$toUpper should leave emoji unchanged"
    ),
    # Special Unicode case mappings not applied (ß does not become SS).
    ToUpperTest(
        "core_eszett",
        value="ß",
        expected="ß",
        msg="$toUpper should not apply special case mapping for eszett",
    ),
    # fi ligature (ﬁ U+FB01) not converted.
    ToUpperTest(
        "core_fi_ligature", value="ﬁ", expected="ﬁ", msg="$toUpper should not convert fi ligature"
    ),
    # Mixed ASCII and non-ASCII: only ASCII converted.
    ToUpperTest(
        "core_mixed_ascii_nonascii",
        value="résumé",
        expected="RéSUMé",
        msg="$toUpper should only convert ASCII letters in mixed string",
    ),
    ToUpperTest(
        "core_mixed_ascii_cjk",
        value="hello世界",
        expected="HELLO世界",
        msg="$toUpper should only convert ASCII letters mixed with CJK",
    ),
    # Zero-width characters preserved.
    # BOM (U+FEFF).
    ToUpperTest(
        "core_bom",
        value="a\ufeffb",
        expected="A\ufeffB",
        msg="$toUpper should preserve BOM character",
    ),
    # Zero-width space (U+200B).
    ToUpperTest(
        "core_zwsp",
        value="a\u200bb",
        expected="A\u200bB",
        msg="$toUpper should preserve zero-width space",
    ),
    # Zero-width joiner (U+200D).
    ToUpperTest(
        "core_zwj",
        value="a\u200db",
        expected="A\u200dB",
        msg="$toUpper should preserve zero-width joiner",
    ),
    # Left-to-right mark (U+200E).
    ToUpperTest(
        "core_lrm",
        value="a\u200eb",
        expected="A\u200eB",
        msg="$toUpper should preserve left-to-right mark",
    ),
    # Right-to-left mark (U+200F).
    ToUpperTest(
        "core_rlm",
        value="a\u200fb",
        expected="A\u200fB",
        msg="$toUpper should preserve right-to-left mark",
    ),
    # ZWJ emoji sequence preserved intact (man technologist: U+1F468 U+200D U+1F4BB).
    ToUpperTest(
        "core_zwj_emoji",
        value="\U0001f468\u200d\U0001f4bb",
        expected="\U0001f468\u200d\U0001f4bb",
        msg="$toUpper should preserve ZWJ emoji sequence",
    ),
    # ASCII boundary characters unchanged.
    # Backtick (U+0060) is immediately before 'a' (U+0061).
    ToUpperTest(
        "core_backtick", value="`", expected="`", msg="$toUpper should leave backtick unchanged"
    ),
    # Open brace (U+007B) is immediately after 'z' (U+007A).
    ToUpperTest(
        "core_open_brace", value="{", expected="{", msg="$toUpper should leave open brace unchanged"
    ),
    # At sign (U+0040) is immediately before 'A' (U+0041).
    ToUpperTest(
        "core_at_sign", value="@", expected="@", msg="$toUpper should leave at sign unchanged"
    ),
    # Open bracket (U+005B) is immediately after 'Z' (U+005A).
    ToUpperTest(
        "core_open_bracket",
        value="[",
        expected="[",
        msg="$toUpper should leave open bracket unchanged",
    ),
    # All boundary characters mixed with letters.
    ToUpperTest(
        "core_boundary_mix",
        value="`a{z@A[Z",
        expected="`A{Z@A[Z",
        msg="$toUpper should only convert letters among ASCII boundary characters",
    ),
    # Multi-byte UTF-8 characters: 2-byte (é U+00E9), 3-byte (日 U+65E5), 4-byte (U+1F389).
    ToUpperTest(
        "core_multibyte",
        value="\u00e9\u65e5\U0001f389",
        expected="\u00e9\u65e5\U0001f389",
        msg="$toUpper should leave multi-byte UTF-8 characters unchanged",
    ),
    # Only digits unchanged.
    ToUpperTest(
        "core_only_digits",
        value="1234567890",
        expected="1234567890",
        msg="$toUpper should leave digit-only string unchanged",
    ),
    # Only whitespace unchanged.
    ToUpperTest(
        "core_only_whitespace",
        value="   \t\n  ",
        expected="   \t\n  ",
        msg="$toUpper should leave whitespace-only string unchanged",
    ),
    # Mixed alphanumeric: only ASCII letters uppercased.
    ToUpperTest(
        "core_mixed_alphanumeric",
        value="abc123def",
        expected="ABC123DEF",
        msg="$toUpper should uppercase only letters in alphanumeric string",
    ),
    # Leading and trailing whitespace preserved.
    ToUpperTest(
        "core_leading_trailing_whitespace",
        value="  hello  ",
        expected="  HELLO  ",
        msg="$toUpper should preserve leading and trailing whitespace",
    ),
]

# Property [Combining Characters]: ASCII base characters are uppercased while combining marks are
# preserved; precomposed characters and non-ASCII bases are not converted.
TOUPPER_COMBINING_TESTS: list[ToUpperTest] = [
    # ASCII base + combining acute accent (U+0301): base uppercased, mark preserved.
    ToUpperTest(
        "combining_ascii_base_acute",
        value="e\u0301",
        expected="E\u0301",
        msg="$toUpper should uppercase ASCII base with combining acute",
    ),
    # ASCII base + combining diaeresis (U+0308): base uppercased, mark preserved.
    ToUpperTest(
        "combining_ascii_base_diaeresis",
        value="a\u0308",
        expected="A\u0308",
        msg="$toUpper should uppercase ASCII base with combining diaeresis",
    ),
    # Precomposed é (U+00E9) is not converted.
    ToUpperTest(
        "combining_precomposed_e_acute",
        value="\u00e9",
        expected="\u00e9",
        msg="$toUpper should not convert precomposed e-acute",
    ),
    # Precomposed ä (U+00E4) is not converted.
    ToUpperTest(
        "combining_precomposed_a_umlaut",
        value="\u00e4",
        expected="\u00e4",
        msg="$toUpper should not convert precomposed a-umlaut",
    ),
    # Combining mark alone (U+0301) is preserved.
    ToUpperTest(
        "combining_mark_alone",
        value="\u0301",
        expected="\u0301",
        msg="$toUpper should preserve combining mark alone",
    ),
    # Non-ASCII base (α U+03B1) + combining mark: not converted.
    ToUpperTest(
        "combining_nonascii_base",
        value="\u03b1\u0301",
        expected="\u03b1\u0301",
        msg="$toUpper should not convert non-ASCII base with combining mark",
    ),
]

# Property [Identity]: empty strings and already-uppercase strings return unchanged.
TOUPPER_IDENTITY_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "identity_empty", value="", expected="", msg="$toUpper should return empty string unchanged"
    ),
    ToUpperTest(
        "identity_uppercase",
        value="HELLO",
        expected="HELLO",
        msg="$toUpper should return uppercase string unchanged",
    ),
    ToUpperTest(
        "identity_uppercase_with_space",
        value="HELLO WORLD",
        expected="HELLO WORLD",
        msg="$toUpper should return uppercase string with spaces unchanged",
    ),
    ToUpperTest(
        "identity_uppercase_with_digits",
        value="ABC123",
        expected="ABC123",
        msg="$toUpper should return uppercase string with digits unchanged",
    ),
]

TOUPPER_CHARACTER_TESTS = TOUPPER_CORE_TESTS + TOUPPER_COMBINING_TESTS + TOUPPER_IDENTITY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(TOUPPER_CHARACTER_TESTS))
def test_toupper_characters(collection, test_case: ToUpperTest):
    """Test $toUpper character conversion behavior."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
