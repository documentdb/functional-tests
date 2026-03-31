from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.ltrim.utils.ltrim_common import (
    LtrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Default Trimming]: when chars is omitted, leading whitespace is trimmed. The default
# set includes ASCII whitespace (space, tab, newline, carriage return, form feed, vertical tab),
# the null byte (U+0000), non-breaking space (U+00A0), and Unicode "Zs" category spaces.
LTRIM_DEFAULT_TRIM_TESTS: list[LtrimTest] = [
    # ASCII whitespace characters.
    LtrimTest(
        "default_space",
        input=" hello",
        expected="hello",
        msg="$ltrim should trim leading space by default",
    ),
    LtrimTest(
        "default_tab",
        input="\thello",
        expected="hello",
        msg="$ltrim should trim leading tab by default",
    ),
    LtrimTest(
        "default_newline",
        input="\nhello",
        expected="hello",
        msg="$ltrim should trim leading newline by default",
    ),
    LtrimTest(
        "default_cr",
        input="\rhello",
        expected="hello",
        msg="$ltrim should trim leading carriage return by default",
    ),
    LtrimTest(
        "default_form_feed",
        input="\fhello",
        expected="hello",
        msg="$ltrim should trim leading form feed by default",
    ),
    LtrimTest(
        "default_vertical_tab",
        input="\x0bhello",
        expected="hello",
        msg="$ltrim should trim leading vertical tab by default",
    ),
    # Null byte (U+0000).
    LtrimTest(
        "default_null_byte",
        input="\x00hello",
        expected="hello",
        msg="$ltrim should trim leading null byte by default",
    ),
    # Non-breaking space (U+00A0).
    LtrimTest(
        "default_nbsp",
        input="\u00a0hello",
        expected="hello",
        msg="$ltrim should trim leading non-breaking space by default",
    ),
    # Unicode "Zs" category spaces.
    LtrimTest(
        "default_en_space",
        input="\u2000hello",
        expected="hello",
        msg="$ltrim should trim leading en space (U+2000) by default",
    ),
    LtrimTest(
        "default_em_space",
        input="\u2003hello",
        expected="hello",
        msg="$ltrim should trim leading em space (U+2003) by default",
    ),
    LtrimTest(
        "default_thin_space",
        input="\u2009hello",
        expected="hello",
        msg="$ltrim should trim leading thin space (U+2009) by default",
    ),
    LtrimTest(
        "default_hair_space",
        input="\u200ahello",
        expected="hello",
        msg="$ltrim should trim leading hair space (U+200A) by default",
    ),
    LtrimTest(
        "default_ogham_space",
        input="\u1680hello",
        expected="hello",
        msg="$ltrim should trim leading ogham space (U+1680) by default",
    ),
    LtrimTest(
        "default_em_quad",
        input="\u2001hello",
        expected="hello",
        msg="$ltrim should trim leading em quad (U+2001) by default",
    ),
    LtrimTest(
        "default_en_space_2002",
        input="\u2002hello",
        expected="hello",
        msg="$ltrim should trim leading en space (U+2002) by default",
    ),
    LtrimTest(
        "default_three_per_em",
        input="\u2004hello",
        expected="hello",
        msg="$ltrim should trim leading three-per-em space (U+2004) by default",
    ),
    LtrimTest(
        "default_four_per_em",
        input="\u2005hello",
        expected="hello",
        msg="$ltrim should trim leading four-per-em space (U+2005) by default",
    ),
    LtrimTest(
        "default_six_per_em",
        input="\u2006hello",
        expected="hello",
        msg="$ltrim should trim leading six-per-em space (U+2006) by default",
    ),
    LtrimTest(
        "default_figure_space",
        input="\u2007hello",
        expected="hello",
        msg="$ltrim should trim leading figure space (U+2007) by default",
    ),
    LtrimTest(
        "default_punctuation_space",
        input="\u2008hello",
        expected="hello",
        msg="$ltrim should trim leading punctuation space (U+2008) by default",
    ),
    # Multiple mixed whitespace characters.
    LtrimTest(
        "default_mixed_ascii_whitespace",
        input=" \t\n\r\f\x0bhello",
        expected="hello",
        msg="$ltrim should trim all mixed ASCII whitespace from leading edge",
    ),
    LtrimTest(
        "default_mixed_unicode_whitespace",
        input="\u00a0\u2000\u2003hello",
        expected="hello",
        msg="$ltrim should trim mixed Unicode whitespace from leading edge",
    ),
    LtrimTest(
        "default_mixed_ascii_and_unicode",
        input=" \t\u00a0\u2000hello",
        expected="hello",
        msg="$ltrim should trim mixed ASCII and Unicode whitespace from leading edge",
    ),
    # All 20 default whitespace code points as a leading prefix.
    LtrimTest(
        "default_all_20_mixed",
        input=(
            "\x00\t\n\x0b\f\r \u00a0\u1680\u2000\u2001\u2002"
            "\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200ahello"
        ),
        expected="hello",
        msg="$ltrim should trim all 20 default whitespace code points from leading edge",
    ),
]

# Property [Default Trimming - exclusions]: characters not in the default whitespace set are
# preserved as leading characters.
LTRIM_DEFAULT_TRIM_EXCLUSION_TESTS: list[LtrimTest] = [
    # Zero-width space (U+200B).
    LtrimTest(
        "default_excl_zwsp",
        input="\u200bhello",
        expected="\u200bhello",
        msg="$ltrim should not trim zero-width space (U+200B) by default",
    ),
    # Line separator (U+2028).
    LtrimTest(
        "default_excl_line_separator",
        input="\u2028hello",
        expected="\u2028hello",
        msg="$ltrim should not trim line separator (U+2028) by default",
    ),
    # Paragraph separator (U+2029).
    LtrimTest(
        "default_excl_paragraph_separator",
        input="\u2029hello",
        expected="\u2029hello",
        msg="$ltrim should not trim paragraph separator (U+2029) by default",
    ),
    # Next line (U+0085).
    LtrimTest(
        "default_excl_next_line",
        input="\u0085hello",
        expected="\u0085hello",
        msg="$ltrim should not trim next line (U+0085) by default",
    ),
    # Ideographic space (U+3000).
    LtrimTest(
        "default_excl_ideographic_space",
        input="\u3000hello",
        expected="\u3000hello",
        msg="$ltrim should not trim ideographic space (U+3000) by default",
    ),
    # Narrow no-break space (U+202F).
    LtrimTest(
        "default_excl_narrow_nbsp",
        input="\u202fhello",
        expected="\u202fhello",
        msg="$ltrim should not trim narrow no-break space (U+202F) by default",
    ),
    # Medium mathematical space (U+205F).
    LtrimTest(
        "default_excl_medium_math_space",
        input="\u205fhello",
        expected="\u205fhello",
        msg="$ltrim should not trim medium mathematical space (U+205F) by default",
    ),
    # BOM / zero-width no-break space (U+FEFF).
    LtrimTest(
        "default_excl_bom",
        input="\ufeffhello",
        expected="\ufeffhello",
        msg="$ltrim should not trim BOM / zero-width no-break space (U+FEFF) by default",
    ),
]


# Property [Edge Cases]: the operator produces correct results at input extremes: empty strings,
# fully trimmable strings, etc.
LTRIM_EDGE_TESTS: list[LtrimTest] = [
    LtrimTest(
        "edge_empty_default",
        input="",
        expected="",
        msg="$ltrim should return empty string for empty input with default chars",
    ),
    LtrimTest(
        "edge_empty_custom",
        input="",
        chars="abc",
        expected="",
        msg="$ltrim should return empty string for empty input with custom chars",
    ),
    LtrimTest(
        "edge_all_whitespace",
        input="   ",
        expected="",
        msg="$ltrim should return empty string when input is all whitespace",
    ),
    LtrimTest(
        "edge_all_in_chars",
        input="aaabbb",
        chars="ab",
        expected="",
        msg="$ltrim should return empty string when all characters are in trim set",
    ),
    # Null byte in custom chars is not treated as a C-style string terminator.
    LtrimTest(
        "edge_null_byte_custom",
        input="\x00\x00hello",
        chars="\x00",
        expected="hello",
        msg="$ltrim should trim null bytes without treating them as C-string terminators",
    ),
    # Control character stops default trimming even if followed by whitespace.
    LtrimTest(
        "edge_control_char_stops_trim",
        input="\x01 hello",
        expected="\x01 hello",
        msg="$ltrim should not trim control character U+0001 by default",
    ),
    # Leading space trimmed, control character stops further trimming.
    LtrimTest(
        "edge_space_then_control_char",
        input=" \x01hello",
        expected="\x01hello",
        msg="$ltrim should trim leading space but stop at control character",
    ),
]

LTRIM_DEFAULT_TRIM_ALL_TESTS = (
    LTRIM_DEFAULT_TRIM_TESTS + LTRIM_DEFAULT_TRIM_EXCLUSION_TESTS + LTRIM_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_DEFAULT_TRIM_ALL_TESTS))
def test_ltrim_default_trim(collection, test_case: LtrimTest):
    """Test $ltrim default trimming and edge cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
