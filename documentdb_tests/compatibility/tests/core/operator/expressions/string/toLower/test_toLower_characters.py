from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.toLower.utils.toLower_common import (
    ToLowerTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Core Conversion Behavior]: only ASCII uppercase letters A-Z are converted to lowercase;
# all other characters are unchanged.
TOLOWER_CORE_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "core_ascii_upper",
        value="HELLO",
        expected="hello",
        msg="$toLower should convert ASCII uppercase to lowercase",
    ),
    ToLowerTest(
        "core_mixed_case",
        value="Hello World",
        expected="hello world",
        msg="$toLower should convert mixed case to lowercase",
    ),
    ToLowerTest(
        "core_digits", value="12345", expected="12345", msg="$toLower should leave digits unchanged"
    ),
    ToLowerTest(
        "core_punctuation",
        value="!@#$%^&*()",
        expected="!@#$%^&*()",
        msg="$toLower should leave punctuation unchanged",
    ),
    ToLowerTest(
        "core_whitespace",
        value="hello world\t\n",
        expected="hello world\t\n",
        msg="$toLower should preserve whitespace characters",
    ),
    # U+00A0 non-breaking space, U+2002 en space, U+2003 em space.
    ToLowerTest(
        "core_unicode_whitespace_nbsp",
        value="A\u00a0B",
        expected="a\u00a0b",
        msg="$toLower should preserve non-breaking space",
    ),
    ToLowerTest(
        "core_unicode_whitespace_en_em",
        value="A\u2002B\u2003C",
        expected="a\u2002b\u2003c",
        msg="$toLower should preserve en space and em space",
    ),
    # Control characters U+0001, U+0002, U+001F.
    ToLowerTest(
        "core_control_chars",
        value="\x01\x02\x1f",
        expected="\x01\x02\x1f",
        msg="$toLower should leave control characters unchanged",
    ),
    # Non-ASCII Unicode letters with case folding are not converted.
    ToLowerTest(
        "core_mixed_ascii_nonascii",
        value="RÉSUMÉ",
        expected="rÉsumÉ",
        msg="$toLower should only convert ASCII letters in mixed string",
    ),
    # Greek uppercase Sigma, Omega, Pi.
    ToLowerTest(
        "core_greek_unchanged",
        value="ΣΩΠ",
        expected="ΣΩΠ",
        msg="$toLower should not convert Greek uppercase letters",
    ),
    # Cyrillic uppercase De, Zhe.
    ToLowerTest(
        "core_cyrillic_unchanged",
        value="ДЖ",
        expected="ДЖ",
        msg="$toLower should not convert Cyrillic uppercase letters",
    ),
    # Deseret capital letter long I (U+10400).
    ToLowerTest(
        "core_deseret_unchanged",
        value="\U00010400",
        expected="\U00010400",
        msg="$toLower should not convert Deseret capital letter",
    ),
    # Latin extended: ñ.
    ToLowerTest(
        "core_latin_extended_lower_unchanged",
        value="ñ",
        expected="ñ",
        msg="$toLower should leave Latin extended lowercase unchanged",
    ),
    # CJK and emoji pass through.
    ToLowerTest(
        "core_cjk_unchanged",
        value="日本語",
        expected="日本語",
        msg="$toLower should leave CJK characters unchanged",
    ),
    ToLowerTest(
        "core_emoji_unchanged",
        value="🎉🚀",
        expected="🎉🚀",
        msg="$toLower should leave emoji unchanged",
    ),
    # Special Unicode case mappings are not applied.
    ToLowerTest(
        "core_eszett_no_expansion",
        value="ß",
        expected="ß",
        msg="$toLower should not apply special case mapping for eszett",
    ),
    # U+FB01 Latin small ligature fi.
    ToLowerTest(
        "core_fi_ligature_no_expansion",
        value="\ufb01",
        expected="\ufb01",
        msg="$toLower should not expand fi ligature",
    ),
    # U+0130 Latin capital letter I with dot above.
    ToLowerTest(
        "core_turkish_i_no_mapping",
        value="\u0130",
        expected="\u0130",
        msg="$toLower should not apply Turkish I mapping",
    ),
    # Zero-width characters: BOM (U+FEFF), ZWSP (U+200B), ZWJ (U+200D), LRM (U+200E),
    # RLM (U+200F).
    ToLowerTest(
        "core_bom", value="\ufeff", expected="\ufeff", msg="$toLower should preserve BOM character"
    ),
    ToLowerTest(
        "core_zwsp",
        value="\u200b",
        expected="\u200b",
        msg="$toLower should preserve zero-width space",
    ),
    ToLowerTest(
        "core_zwj",
        value="\u200d",
        expected="\u200d",
        msg="$toLower should preserve zero-width joiner",
    ),
    ToLowerTest(
        "core_lrm",
        value="\u200e",
        expected="\u200e",
        msg="$toLower should preserve left-to-right mark",
    ),
    ToLowerTest(
        "core_rlm",
        value="\u200f",
        expected="\u200f",
        msg="$toLower should preserve right-to-left mark",
    ),
    # ZWJ emoji sequence: man + ZWJ + woman + ZWJ + girl.
    ToLowerTest(
        "core_zwj_emoji_sequence",
        value="\U0001f468\u200d\U0001f469\u200d\U0001f467",
        expected="\U0001f468\u200d\U0001f469\u200d\U0001f467",
        msg="$toLower should preserve ZWJ emoji sequence",
    ),
    # ASCII boundary characters: backtick (U+0060) before 'a', '{' (U+007B) after 'z',
    # '@' (U+0040) before 'A', '[' (U+005B) after 'Z'.
    ToLowerTest(
        "core_backtick_before_a",
        value="`",
        expected="`",
        msg="$toLower should leave backtick unchanged",
    ),
    ToLowerTest(
        "core_lbrace_after_z",
        value="{",
        expected="{",
        msg="$toLower should leave open brace unchanged",
    ),
    ToLowerTest(
        "core_at_before_A", value="@", expected="@", msg="$toLower should leave at sign unchanged"
    ),
    ToLowerTest(
        "core_lbracket_after_Z",
        value="[",
        expected="[",
        msg="$toLower should leave open bracket unchanged",
    ),
    # Multi-byte UTF-8: 2-byte (U+00E9).
    ToLowerTest(
        "core_2byte_utf8",
        value="\u00e9",
        expected="\u00e9",
        msg="$toLower should leave 2-byte UTF-8 character unchanged",
    ),
    # Embedded null byte (U+0000) preserved, surrounding characters still converted.
    ToLowerTest(
        "core_embedded_null_byte",
        value="A\x00B",
        expected="a\x00b",
        msg="$toLower should preserve embedded null byte",
    ),
]

# Property [Normalization Independence]: the operator processes individual codepoints, not
# normalized or composed grapheme clusters.
TOLOWER_COMBINING_TESTS: list[ToLowerTest] = [
    # A (U+0041) + combining acute accent (U+0301).
    ToLowerTest(
        "combining_ascii_base_with_acute",
        value="A\u0301",
        expected="a\u0301",
        msg="$toLower should lowercase ASCII base with combining acute",
    ),
    # Precomposed É (U+00C9) is a single non-ASCII codepoint, not converted.
    ToLowerTest(
        "combining_precomposed_unchanged",
        value="\u00c9",
        expected="\u00c9",
        msg="$toLower should not convert precomposed E-acute",
    ),
    # Combining acute accent alone (U+0301), no base character.
    ToLowerTest(
        "combining_mark_alone",
        value="\u0301",
        expected="\u0301",
        msg="$toLower should preserve combining mark alone",
    ),
    # Non-ASCII base Σ (U+03A3) + combining acute (U+0301).
    ToLowerTest(
        "combining_nonascii_base_with_mark",
        value="\u03a3\u0301",
        expected="\u03a3\u0301",
        msg="$toLower should not convert non-ASCII base with combining mark",
    ),
]

# Property [Identity]: empty strings and already-lowercase strings return unchanged.
TOLOWER_IDENTITY_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "identity_empty", value="", expected="", msg="$toLower should return empty string unchanged"
    ),
    ToLowerTest(
        "identity_lowercase",
        value="hello",
        expected="hello",
        msg="$toLower should return lowercase string unchanged",
    ),
    ToLowerTest(
        "identity_lowercase_with_space",
        value="hello world",
        expected="hello world",
        msg="$toLower should return lowercase string with spaces unchanged",
    ),
    ToLowerTest(
        "identity_lowercase_with_digits",
        value="abc123",
        expected="abc123",
        msg="$toLower should return lowercase string with digits unchanged",
    ),
]

TOLOWER_CHARACTER_TESTS = TOLOWER_CORE_TESTS + TOLOWER_COMBINING_TESTS + TOLOWER_IDENTITY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(TOLOWER_CHARACTER_TESTS))
def test_tolower_characters(collection, test_case: ToLowerTest):
    """Test $toLower character conversion behavior."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
