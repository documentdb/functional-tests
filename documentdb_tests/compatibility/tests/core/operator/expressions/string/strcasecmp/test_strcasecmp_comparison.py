from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.strcasecmp_common import (
    StrcasecmpTest,
    _expr,
)

# Property [Comparison Semantics]: comparison is lexicographic by code point,
# case-insensitive for ASCII letters only (not Unicode).
STRCASECMP_COMPARISON_TESTS: list[StrcasecmpTest] = [
    # ASCII case folding.
    StrcasecmpTest(
        "cmp_ascii_upper_vs_lower",
        string1="ABC",
        string2="abc",
        expected=0,
        msg="$strcasecmp should fold ASCII uppercase to match lowercase",
    ),
    StrcasecmpTest(
        "cmp_ascii_lower_vs_upper",
        string1="abc",
        string2="ABC",
        expected=0,
        msg="$strcasecmp should fold ASCII lowercase to match uppercase",
    ),
    StrcasecmpTest(
        "cmp_ascii_mixed_case",
        string1="AbC",
        string2="aBc",
        expected=0,
        msg="$strcasecmp should fold mixed ASCII case to equal",
    ),
    # Lexicographic ordering.
    StrcasecmpTest(
        "cmp_less",
        string1="apple",
        string2="banana",
        expected=-1,
        msg="$strcasecmp should return -1 when first string is lexicographically less",
    ),
    StrcasecmpTest(
        "cmp_greater",
        string1="banana",
        string2="apple",
        expected=1,
        msg="$strcasecmp should return 1 when first string is lexicographically greater",
    ),
    StrcasecmpTest(
        "cmp_equal",
        string1="same",
        string2="same",
        expected=0,
        msg="$strcasecmp should return 0 for identical strings",
    ),
    # Prefix is less than longer string.
    StrcasecmpTest(
        "cmp_prefix_shorter",
        string1="abc",
        string2="abcd",
        expected=-1,
        msg="$strcasecmp should rank a prefix before the longer string",
    ),
    StrcasecmpTest(
        "cmp_prefix_longer",
        string1="abcd",
        string2="abc",
        expected=1,
        msg="$strcasecmp should rank a longer string after its prefix",
    ),
    # Non-ASCII uppercase/lowercase are NOT folded.
    # U+00C9 (É) vs U+00E9 (é)
    StrcasecmpTest(
        "cmp_non_ascii_e_accent",
        string1="\u00c9",
        string2="\u00e9",
        expected=-1,
        msg="$strcasecmp should not fold non-ASCII É (U+00C9) to é (U+00E9)",
    ),
    # U+00D1 (Ñ) vs U+00F1 (ñ)
    StrcasecmpTest(
        "cmp_non_ascii_n_tilde",
        string1="\u00d1",
        string2="\u00f1",
        expected=-1,
        msg="$strcasecmp should not fold non-ASCII Ñ (U+00D1) to ñ (U+00F1)",
    ),
    # Cyrillic U+0410 (А) vs U+0430 (а)
    StrcasecmpTest(
        "cmp_non_ascii_cyrillic",
        string1="\u0410",
        string2="\u0430",
        expected=-1,
        msg="$strcasecmp should not fold Cyrillic А (U+0410) to а (U+0430)",
    ),
    # No Unicode case folding: ß (U+00DF) != ss.
    StrcasecmpTest(
        "cmp_no_fold_sharp_s",
        string1="\u00df",
        string2="ss",
        expected=1,
        msg="$strcasecmp should not fold ß (U+00DF) to ss",
    ),
    # Turkish dotless i not folded: İ (U+0130) != i.
    StrcasecmpTest(
        "cmp_no_fold_turkish_i",
        string1="\u0130",
        string2="i",
        expected=1,
        msg="$strcasecmp should not fold İ (U+0130) to i",
    ),
]

# Property [Encoding and Character Handling]: multi-byte UTF-8 characters are
# compared by code point value, and precomposed vs decomposed forms are distinct.
STRCASECMP_ENCODING_TESTS: list[StrcasecmpTest] = [
    # 2-byte UTF-8: é (U+00E9)
    StrcasecmpTest(
        "enc_2byte_equal",
        string1="\u00e9",
        string2="\u00e9",
        expected=0,
        msg="$strcasecmp should return 0 for identical 2-byte UTF-8 characters",
    ),
    StrcasecmpTest(
        "enc_2byte_vs_ascii",
        string1="\u00e9",
        string2="e",
        expected=1,
        msg="$strcasecmp should rank 2-byte é (U+00E9) after ASCII 'e'",
    ),
    # 3-byte UTF-8: ☺ (U+263A)
    StrcasecmpTest(
        "enc_3byte_equal",
        string1="\u263a",
        string2="\u263a",
        expected=0,
        msg="$strcasecmp should return 0 for identical 3-byte UTF-8 characters",
    ),
    StrcasecmpTest(
        "enc_3byte_vs_ascii",
        string1="\u263a",
        string2="a",
        expected=1,
        msg="$strcasecmp should rank 3-byte ☺ (U+263A) after ASCII 'a'",
    ),
    # 4-byte UTF-8: 𝄞 (U+1D11E)
    StrcasecmpTest(
        "enc_4byte_equal",
        string1="\U0001d11e",
        string2="\U0001d11e",
        expected=0,
        msg="$strcasecmp should return 0 for identical 4-byte UTF-8 characters",
    ),
    StrcasecmpTest(
        "enc_4byte_vs_ascii",
        string1="\U0001d11e",
        string2="a",
        expected=1,
        msg="$strcasecmp should rank 4-byte 𝄞 (U+1D11E) after ASCII 'a'",
    ),
    # Precomposed (U+00E9) vs decomposed (U+0065 + U+0301) are distinct.
    StrcasecmpTest(
        "enc_precomposed_vs_decomposed",
        string1="\u00e9",
        string2="e\u0301",
        expected=1,
        msg="$strcasecmp should distinguish precomposed é from decomposed e+combining accent",
    ),
    # Null bytes are preserved and compared.
    StrcasecmpTest(
        "enc_null_byte_equal",
        string1="\x00",
        string2="\x00",
        expected=0,
        msg="$strcasecmp should return 0 for identical null bytes",
    ),
    StrcasecmpTest(
        "enc_null_byte_vs_empty",
        string1="\x00",
        string2="",
        expected=1,
        msg="$strcasecmp should rank null byte after empty string",
    ),
    StrcasecmpTest(
        "enc_null_byte_vs_ascii",
        string1="\x00",
        string2="a",
        expected=-1,
        msg="$strcasecmp should rank null byte before ASCII 'a'",
    ),
    StrcasecmpTest(
        "enc_embedded_null_byte",
        string1="a\x00b",
        string2="a\x00c",
        expected=-1,
        msg="$strcasecmp should compare characters after embedded null bytes",
    ),
]

# Property [Edge Cases]: comparison behaves correctly at boundary conditions
# such as empty strings, large inputs, and special characters.
STRCASECMP_EDGE_TESTS: list[StrcasecmpTest] = [
    StrcasecmpTest(
        "edge_both_empty",
        string1="",
        string2="",
        expected=0,
        msg="$strcasecmp should return 0 for two empty strings",
    ),
    StrcasecmpTest(
        "edge_empty_vs_nonempty",
        string1="",
        string2="a",
        expected=-1,
        msg="$strcasecmp should rank empty string before non-empty",
    ),
    StrcasecmpTest(
        "edge_nonempty_vs_empty",
        string1="a",
        string2="",
        expected=1,
        msg="$strcasecmp should rank non-empty string after empty",
    ),
    # Whitespace and control characters compared by code point.
    StrcasecmpTest(
        "edge_newline_vs_tab",
        string1="\n",
        string2="\t",
        expected=1,
        msg="$strcasecmp should rank newline after tab by code point",
    ),
    StrcasecmpTest(
        "edge_tab_vs_newline",
        string1="\t",
        string2="\n",
        expected=-1,
        msg="$strcasecmp should rank tab before newline by code point",
    ),
    StrcasecmpTest(
        "edge_space_vs_letter",
        string1=" ",
        string2="a",
        expected=-1,
        msg="$strcasecmp should rank space before letter by code point",
    ),
    StrcasecmpTest(
        "edge_trailing_space",
        string1="a ",
        string2="a",
        expected=1,
        msg="$strcasecmp should rank string with trailing space after same string without",
    ),
    # Digit strings are lexicographic, not numeric.
    StrcasecmpTest(
        "edge_digit_lexicographic",
        string1="9",
        string2="10",
        expected=1,
        msg="$strcasecmp should compare '9' > '10' lexicographically",
    ),
    StrcasecmpTest(
        "edge_digit_order",
        string1="1",
        string2="2",
        expected=-1,
        msg="$strcasecmp should compare '1' < '2' lexicographically",
    ),
]

STRCASECMP_COMPARISON_ALL_TESTS = (
    STRCASECMP_COMPARISON_TESTS + STRCASECMP_ENCODING_TESTS + STRCASECMP_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_COMPARISON_ALL_TESTS))
def test_strcasecmp_comparison_cases(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp comparison, encoding, and edge cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
