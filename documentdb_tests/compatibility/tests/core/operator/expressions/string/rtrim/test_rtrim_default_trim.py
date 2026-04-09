from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params

from .utils.rtrim_common import (
    RtrimTest,
    _expr,
)

# Property [Default Trimming]: when chars is omitted, trailing whitespace is trimmed. The default
# set includes ASCII whitespace (space, tab, newline, carriage return, form feed, vertical tab),
# the null byte (U+0000), non-breaking space (U+00A0), and Unicode "Zs" category spaces.
RTRIM_DEFAULT_TRIM_TESTS: list[RtrimTest] = [
    # ASCII whitespace characters.
    RtrimTest(
        "default_space",
        input="hello ",
        expected="hello",
        msg="$rtrim should trim trailing space by default",
    ),
    RtrimTest(
        "default_tab",
        input="hello\t",
        expected="hello",
        msg="$rtrim should trim trailing tab by default",
    ),
    RtrimTest(
        "default_newline",
        input="hello\n",
        expected="hello",
        msg="$rtrim should trim trailing newline by default",
    ),
    RtrimTest(
        "default_cr",
        input="hello\r",
        expected="hello",
        msg="$rtrim should trim trailing carriage return by default",
    ),
    RtrimTest(
        "default_form_feed",
        input="hello\f",
        expected="hello",
        msg="$rtrim should trim trailing form feed by default",
    ),
    RtrimTest(
        "default_vertical_tab",
        input="hello\x0b",
        expected="hello",
        msg="$rtrim should trim trailing vertical tab by default",
    ),
    # Null byte (U+0000).
    RtrimTest(
        "default_null_byte",
        input="hello\x00",
        expected="hello",
        msg="$rtrim should trim trailing null byte by default",
    ),
    # Non-breaking space (U+00A0).
    RtrimTest(
        "default_nbsp",
        input="hello\u00a0",
        expected="hello",
        msg="$rtrim should trim trailing non-breaking space by default",
    ),
    # Unicode "Zs" category spaces.
    RtrimTest(
        "default_en_space",
        input="hello\u2000",
        expected="hello",
        msg="$rtrim should trim trailing en space (U+2000) by default",
    ),
    RtrimTest(
        "default_em_space",
        input="hello\u2003",
        expected="hello",
        msg="$rtrim should trim trailing em space (U+2003) by default",
    ),
    RtrimTest(
        "default_thin_space",
        input="hello\u2009",
        expected="hello",
        msg="$rtrim should trim trailing thin space (U+2009) by default",
    ),
    RtrimTest(
        "default_hair_space",
        input="hello\u200a",
        expected="hello",
        msg="$rtrim should trim trailing hair space (U+200A) by default",
    ),
    RtrimTest(
        "default_ogham_space",
        input="hello\u1680",
        expected="hello",
        msg="$rtrim should trim trailing ogham space (U+1680) by default",
    ),
    RtrimTest(
        "default_em_quad",
        input="hello\u2001",
        expected="hello",
        msg="$rtrim should trim trailing em quad (U+2001) by default",
    ),
    RtrimTest(
        "default_en_space_2002",
        input="hello\u2002",
        expected="hello",
        msg="$rtrim should trim trailing en space (U+2002) by default",
    ),
    RtrimTest(
        "default_three_per_em",
        input="hello\u2004",
        expected="hello",
        msg="$rtrim should trim trailing three-per-em space (U+2004) by default",
    ),
    RtrimTest(
        "default_four_per_em",
        input="hello\u2005",
        expected="hello",
        msg="$rtrim should trim trailing four-per-em space (U+2005) by default",
    ),
    RtrimTest(
        "default_six_per_em",
        input="hello\u2006",
        expected="hello",
        msg="$rtrim should trim trailing six-per-em space (U+2006) by default",
    ),
    RtrimTest(
        "default_figure_space",
        input="hello\u2007",
        expected="hello",
        msg="$rtrim should trim trailing figure space (U+2007) by default",
    ),
    RtrimTest(
        "default_punctuation_space",
        input="hello\u2008",
        expected="hello",
        msg="$rtrim should trim trailing punctuation space (U+2008) by default",
    ),
    # Multiple mixed whitespace characters.
    RtrimTest(
        "default_mixed_ascii_whitespace",
        input="hello \t\n\r\f\x0b",
        expected="hello",
        msg="$rtrim should trim all mixed ASCII whitespace from trailing edge",
    ),
    RtrimTest(
        "default_mixed_unicode_whitespace",
        input="hello\u00a0\u2000\u2003",
        expected="hello",
        msg="$rtrim should trim mixed Unicode whitespace from trailing edge",
    ),
    RtrimTest(
        "default_mixed_ascii_and_unicode",
        input="hello \t\u00a0\u2000",
        expected="hello",
        msg="$rtrim should trim mixed ASCII and Unicode whitespace from trailing edge",
    ),
    # All 20 default whitespace code points as a trailing suffix.
    RtrimTest(
        "default_all_20_mixed",
        input=(
            "hello\x00\t\n\x0b\f\r \u00a0\u1680\u2000\u2001\u2002"
            "\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
        ),
        expected="hello",
        msg="$rtrim should trim all 20 default whitespace code points from trailing edge",
    ),
]

# Property [Default Trimming - exclusions]: characters not in the default whitespace set are
# preserved as trailing characters.
RTRIM_DEFAULT_TRIM_EXCLUSION_TESTS: list[RtrimTest] = [
    # Zero-width space (U+200B).
    RtrimTest(
        "default_excl_zwsp",
        input="hello\u200b",
        expected="hello\u200b",
        msg="$rtrim should not trim zero-width space (U+200B) by default",
    ),
    # Line separator (U+2028).
    RtrimTest(
        "default_excl_line_separator",
        input="hello\u2028",
        expected="hello\u2028",
        msg="$rtrim should not trim line separator (U+2028) by default",
    ),
    # Paragraph separator (U+2029).
    RtrimTest(
        "default_excl_paragraph_separator",
        input="hello\u2029",
        expected="hello\u2029",
        msg="$rtrim should not trim paragraph separator (U+2029) by default",
    ),
    # Next line (U+0085).
    RtrimTest(
        "default_excl_next_line",
        input="hello\u0085",
        expected="hello\u0085",
        msg="$rtrim should not trim next line (U+0085) by default",
    ),
    # Ideographic space (U+3000).
    RtrimTest(
        "default_excl_ideographic_space",
        input="hello\u3000",
        expected="hello\u3000",
        msg="$rtrim should not trim ideographic space (U+3000) by default",
    ),
    # Narrow no-break space (U+202F).
    RtrimTest(
        "default_excl_narrow_nbsp",
        input="hello\u202f",
        expected="hello\u202f",
        msg="$rtrim should not trim narrow no-break space (U+202F) by default",
    ),
    # Medium mathematical space (U+205F).
    RtrimTest(
        "default_excl_medium_math_space",
        input="hello\u205f",
        expected="hello\u205f",
        msg="$rtrim should not trim medium mathematical space (U+205F) by default",
    ),
    # BOM / zero-width no-break space (U+FEFF).
    RtrimTest(
        "default_excl_bom",
        input="hello\ufeff",
        expected="hello\ufeff",
        msg="$rtrim should not trim BOM / zero-width no-break space (U+FEFF) by default",
    ),
]


# Property [Edge Cases]: the operator produces correct results at input extremes: empty strings,
# fully trimmable strings, and large inputs.
RTRIM_EDGE_TESTS: list[RtrimTest] = [
    RtrimTest(
        "edge_empty_default",
        input="",
        expected="",
        msg="$rtrim should return empty string for empty input with default chars",
    ),
    RtrimTest(
        "edge_empty_custom",
        input="",
        chars="abc",
        expected="",
        msg="$rtrim should return empty string for empty input with custom chars",
    ),
    RtrimTest(
        "edge_all_whitespace",
        input="   ",
        expected="",
        msg="$rtrim should return empty string when input is all whitespace",
    ),
    RtrimTest(
        "edge_all_in_chars",
        input="aaabbb",
        chars="ab",
        expected="",
        msg="$rtrim should return empty string when all characters are in trim set",
    ),
    # Null byte in custom chars is not treated as a C-style string terminator.
    RtrimTest(
        "edge_null_byte_custom",
        input="hello\x00\x00",
        chars="\x00",
        expected="hello",
        msg="$rtrim should trim null bytes without treating them as C-string terminators",
    ),
    # Control character stops default trimming even if preceded by whitespace.
    RtrimTest(
        "edge_control_char_stops_trim",
        input="hello \x01",
        expected="hello \x01",
        msg="$rtrim should not trim control character U+0001 by default",
    ),
    # Trailing space trimmed, control character stops further trimming.
    RtrimTest(
        "edge_control_char_then_space",
        input="hello\x01 ",
        expected="hello\x01",
        msg="$rtrim should trim trailing space but stop at control character",
    ),
]

RTRIM_DEFAULT_TRIM_ALL_TESTS = (
    RTRIM_DEFAULT_TRIM_TESTS + RTRIM_DEFAULT_TRIM_EXCLUSION_TESTS + RTRIM_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_DEFAULT_TRIM_ALL_TESTS))
def test_rtrim_default_trim(collection, test_case: RtrimTest):
    """Test $rtrim default trimming, exclusions, and edge cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
