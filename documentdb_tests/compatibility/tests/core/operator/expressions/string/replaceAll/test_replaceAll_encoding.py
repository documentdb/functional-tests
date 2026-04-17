from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.replaceAll_common import (
    ReplaceAllTest,
    _expr,
)

# Property [Encoding]: matching is diacritic-sensitive, no Unicode normalization, multi-byte
# characters handled correctly, special and regex characters treated literally.
REPLACEALL_ENCODING_TESTS: list[ReplaceAllTest] = [
    # Diacritic sensitivity.
    ReplaceAllTest(
        "encoding_diacritic_no_match",
        input="café",
        find="cafe",
        replacement="X",
        expected="café",
        msg="$replaceAll should handle diacritic no match",
    ),
    ReplaceAllTest(
        "encoding_diaeresis_no_match",
        input="naïve",
        find="naive",
        replacement="X",
        expected="naïve",
        msg="$replaceAll should handle diaeresis no match",
    ),
    ReplaceAllTest(
        "encoding_diacritic_match_all",
        input="résumé",
        find="é",
        replacement="e",
        expected="resume",
        msg="$replaceAll should handle diacritic match all",
    ),
    ReplaceAllTest(
        "encoding_diacritic_a_no_match",
        input="está",
        find="esta",
        replacement="X",
        expected="está",
        msg="$replaceAll should handle diacritic a no match",
    ),
    ReplaceAllTest(
        "encoding_diacritic_n_no_match",
        input="año",
        find="ano",
        replacement="X",
        expected="año",
        msg="$replaceAll should handle diacritic n no match",
    ),
    # Precomposed U+00E9 does not match decomposed U+0065 U+0301.
    ReplaceAllTest(
        "encoding_precomposed_vs_decomposed",
        input="\u00e9",
        find="e\u0301",
        replacement="X",
        expected="\u00e9",
        msg="$replaceAll should handle precomposed vs decomposed",
    ),
    ReplaceAllTest(
        "encoding_decomposed_vs_precomposed",
        input="e\u0301",
        find="\u00e9",
        replacement="X",
        expected="e\u0301",
        msg="$replaceAll should handle decomposed vs precomposed",
    ),
    # Same representation matches.
    ReplaceAllTest(
        "encoding_precomposed_matches_precomposed",
        input="\u00e9",
        find="\u00e9",
        replacement="X",
        expected="X",
        msg="$replaceAll should handle precomposed matches precomposed",
    ),
    ReplaceAllTest(
        "encoding_decomposed_matches_decomposed",
        input="e\u0301",
        find="e\u0301",
        replacement="X",
        expected="X",
        msg="$replaceAll should handle decomposed matches decomposed",
    ),
    # A base character can be matched independently of a following combining mark.
    ReplaceAllTest(
        "encoding_base_char_splits_combining_mark",
        input="e\u0301",
        find="e",
        replacement="X",
        expected="X\u0301",
        msg="$replaceAll should handle base char splits combining mark",
    ),
    # Combining mark alone (U+0301) is matchable as find.
    ReplaceAllTest(
        "encoding_combining_mark_alone",
        input="e\u0301",
        find="\u0301",
        replacement="X",
        expected="eX",
        msg="$replaceAll should handle combining mark alone",
    ),
    # Multi-byte UTF-8: 3-byte (U+4E16), 4-byte (U+1F600). 2-byte is covered by
    # encoding_diacritic_match_all.
    ReplaceAllTest(
        "encoding_3byte_find",
        input="hello世界世",
        find="世",
        replacement="X",
        expected="helloX界X",
        msg="$replaceAll should handle 3byte find",
    ),
    ReplaceAllTest(
        "encoding_4byte_find",
        input="a😀b😀c",
        find="😀",
        replacement="X",
        expected="aXbXc",
        msg="$replaceAll should handle 4byte find",
    ),
    ReplaceAllTest(
        "encoding_4byte_replacement",
        input="hello",
        find="h",
        replacement="😀",
        expected="😀ello",
        msg="$replaceAll should handle 4byte replacement",
    ),
    # Zero-width and invisible characters treated as regular code points.
    # BOM (U+FEFF).
    ReplaceAllTest(
        "encoding_bom",
        input="a\ufeffb",
        find="\ufeff",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle bom",
    ),
    # ZWSP (U+200B).
    ReplaceAllTest(
        "encoding_zwsp",
        input="a\u200bb",
        find="\u200b",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle zwsp",
    ),
    # ZWJ (U+200D).
    ReplaceAllTest(
        "encoding_zwj",
        input="a\u200db",
        find="\u200d",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle zwj",
    ),
    # LTR mark (U+200E).
    ReplaceAllTest(
        "encoding_ltr_mark",
        input="a\u200eb",
        find="\u200e",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle ltr mark",
    ),
    # RTL mark (U+200F).
    ReplaceAllTest(
        "encoding_rtl_mark",
        input="a\u200fb",
        find="\u200f",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle rtl mark",
    ),
    # ZWJ within emoji sequence can be removed, splitting the sequence.
    # Family emoji: U+1F468 U+200D U+1F469 U+200D U+1F467.
    ReplaceAllTest(
        "encoding_zwj_emoji_split",
        input="\U0001f468\u200d\U0001f469\u200d\U0001f467",
        find="\u200d",
        replacement="",
        expected="\U0001f468\U0001f469\U0001f467",
        msg="$replaceAll should handle zwj emoji split",
    ),
    # Unicode boundary code points.
    # U+FFFF (last BMP code point).
    ReplaceAllTest(
        "encoding_boundary_ffff",
        input="a\uffffb",
        find="\uffff",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle boundary ffff",
    ),
    # U+10000 (first supplementary code point).
    ReplaceAllTest(
        "encoding_boundary_10000",
        input="a\U00010000b",
        find="\U00010000",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle boundary 10000",
    ),
    # U+10FFFF (last valid Unicode code point).
    ReplaceAllTest(
        "encoding_boundary_10ffff",
        input="a\U0010ffffb",
        find="\U0010ffff",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle boundary 10ffff",
    ),
    # Special characters: newline, tab, carriage return, null byte.
    ReplaceAllTest(
        "encoding_newline",
        input="line1\nline2\nline3",
        find="\n",
        replacement=" ",
        expected="line1 line2 line3",
        msg="$replaceAll should handle newline",
    ),
    ReplaceAllTest(
        "encoding_tab",
        input="col1\tcol2\tcol3",
        find="\t",
        replacement=" ",
        expected="col1 col2 col3",
        msg="$replaceAll should handle tab",
    ),
    ReplaceAllTest(
        "encoding_carriage_return",
        input="line1\r\nline2",
        find="\r\n",
        replacement="\n",
        expected="line1\nline2",
        msg="$replaceAll should handle carriage return",
    ),
    # Plain space as explicit find target.
    ReplaceAllTest(
        "encoding_space",
        input="a b c",
        find=" ",
        replacement="X",
        expected="aXbXc",
        msg="$replaceAll should handle space",
    ),
    # NBSP (U+00A0).
    ReplaceAllTest(
        "encoding_nbsp",
        input="a\u00a0b",
        find="\u00a0",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle nbsp",
    ),
    # En space (U+2000).
    ReplaceAllTest(
        "encoding_en_space",
        input="a\u2000b",
        find="\u2000",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle en space",
    ),
    # Em space (U+2003).
    ReplaceAllTest(
        "encoding_em_space",
        input="a\u2003b",
        find="\u2003",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle em space",
    ),
    # No Unicode whitespace equivalence: NBSP does not match regular space.
    ReplaceAllTest(
        "encoding_nbsp_not_space",
        input="a\u00a0b",
        find=" ",
        replacement="X",
        expected="a\u00a0b",
        msg="$replaceAll should handle nbsp not space",
    ),
    # \n alone within CRLF matches only the LF, leaving orphan \r.
    ReplaceAllTest(
        "encoding_lf_within_crlf",
        input="line1\r\nline2",
        find="\n",
        replacement="X",
        expected="line1\rXline2",
        msg="$replaceAll should handle lf within crlf",
    ),
    ReplaceAllTest(
        "encoding_null_byte",
        input="a\x00b\x00c",
        find="\x00",
        replacement="X",
        expected="aXbXc",
        msg="$replaceAll should handle null byte",
    ),
    # Regex-special characters treated literally.
    ReplaceAllTest(
        "encoding_regex_dot",
        input="a.b.c",
        find=".",
        replacement="X",
        expected="aXbXc",
        msg="$replaceAll should handle regex dot",
    ),
    ReplaceAllTest(
        "encoding_regex_dot_star",
        input="a.*b",
        find=".*",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle regex dot star",
    ),
    ReplaceAllTest(
        "encoding_regex_parens_plus",
        input="(a+b)(a+b)",
        find="(a+b)",
        replacement="X",
        expected="XX",
        msg="$replaceAll should handle regex parens plus",
    ),
    ReplaceAllTest(
        "encoding_regex_brackets",
        input="a[0]b[0]",
        find="[0]",
        replacement="X",
        expected="aXbX",
        msg="$replaceAll should handle regex brackets",
    ),
    # Regex-special: ?, |, ^, {, }.
    ReplaceAllTest(
        "encoding_regex_question",
        input="a?b|c^d{e}",
        find="?",
        replacement="X",
        expected="aXb|c^d{e}",
        msg="$replaceAll should handle regex question",
    ),
    ReplaceAllTest(
        "encoding_regex_pipe",
        input="a|b|c",
        find="|",
        replacement="X",
        expected="aXbXc",
        msg="$replaceAll should handle regex pipe",
    ),
    ReplaceAllTest(
        "encoding_regex_caret",
        input="^a^b^",
        find="^",
        replacement="X",
        expected="XaXbX",
        msg="$replaceAll should handle regex caret",
    ),
    # Control character 0x01 (SOH).
    ReplaceAllTest(
        "encoding_control_char_soh",
        input="a\x01b\x01c",
        find="\x01",
        replacement="X",
        expected="aXbXc",
        msg="$replaceAll should handle control char soh",
    ),
    # Control character 0x1F (US).
    ReplaceAllTest(
        "encoding_control_char_us",
        input="a\x1fb",
        find="\x1f",
        replacement="X",
        expected="aXb",
        msg="$replaceAll should handle control char us",
    ),
    # JSON/BSON-significant characters: double quote, braces, dollar sign via $literal.
    ReplaceAllTest(
        "encoding_double_quote",
        input='a"b"c',
        find='"',
        replacement="X",
        expected="aXbXc",
        msg="$replaceAll should handle double quote",
    ),
    ReplaceAllTest(
        "encoding_left_brace",
        input="a{b}c",
        find="{",
        replacement="X",
        expected="aXb}c",
        msg="$replaceAll should handle left brace",
    ),
    ReplaceAllTest(
        "encoding_right_brace",
        input="a{b}c",
        find="}",
        replacement="X",
        expected="a{bXc",
        msg="$replaceAll should handle right brace",
    ),
    # Backslash sequences in replacement treated as literal text, not regex backreferences.
    ReplaceAllTest(
        "encoding_backslash_one_literal",
        input="abc",
        find="b",
        replacement="\\1",
        expected="a\\1c",
        msg="$replaceAll should handle backslash one literal",
    ),
    ReplaceAllTest(
        "encoding_backslash_n_literal",
        input="abc",
        find="b",
        replacement="\\n",
        expected="a\\nc",
        msg="$replaceAll should handle backslash n literal",
    ),
    # Dollar-prefixed strings via $literal in all three parameters.
    ReplaceAllTest(
        "encoding_dollar_literal_input",
        input={"$literal": "$hello"},
        find={"$literal": "$hello"},
        replacement="X",
        expected="X",
        msg="$replaceAll should handle dollar literal input",
    ),
    ReplaceAllTest(
        "encoding_dollar_literal_find",
        input={"$literal": "$hello world"},
        find={"$literal": "$hello"},
        replacement="X",
        expected="X world",
        msg="$replaceAll should handle dollar literal find",
    ),
    ReplaceAllTest(
        "encoding_dollar_literal_replacement",
        input="hello",
        find="hello",
        replacement={"$literal": "$world"},
        expected="$world",
        msg="$replaceAll should handle dollar literal replacement",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_ENCODING_TESTS))
def test_replaceall_encoding_cases(collection, test_case: ReplaceAllTest):
    """Test $replaceAll encoding cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
