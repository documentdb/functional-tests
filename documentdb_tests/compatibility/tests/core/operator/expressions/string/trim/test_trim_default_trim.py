from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params

from .utils.trim_common import (
    TrimTest,
    _expr,
)

# Property [Default Trimming]: when chars is omitted, whitespace is trimmed from both ends. The
# default set includes ASCII whitespace (space, tab, newline, carriage return, form feed,
# vertical tab), the null byte (U+0000), non-breaking space (U+00A0), and Unicode "Zs" category
# spaces.
TRIM_DEFAULT_TRIM_TESTS: list[TrimTest] = [
    # ASCII whitespace characters.
    TrimTest(
        "default_space",
        input=" hello ",
        expected="hello",
        msg="$trim should trim surrounding spaces by default",
    ),
    TrimTest(
        "default_tab",
        input="\thello\t",
        expected="hello",
        msg="$trim should trim surrounding tabs by default",
    ),
    TrimTest(
        "default_newline",
        input="\nhello\n",
        expected="hello",
        msg="$trim should trim surrounding newlines by default",
    ),
    TrimTest(
        "default_cr",
        input="\rhello\r",
        expected="hello",
        msg="$trim should trim surrounding carriage returns by default",
    ),
    TrimTest(
        "default_form_feed",
        input="\fhello\f",
        expected="hello",
        msg="$trim should trim surrounding form feeds by default",
    ),
    TrimTest(
        "default_vertical_tab",
        input="\x0bhello\x0b",
        expected="hello",
        msg="$trim should trim surrounding vertical tabs by default",
    ),
    # Null byte (U+0000).
    TrimTest(
        "default_null_byte",
        input="\x00hello\x00",
        expected="hello",
        msg="$trim should trim surrounding null bytes by default",
    ),
    # Non-breaking space (U+00A0).
    TrimTest(
        "default_nbsp",
        input="\u00a0hello\u00a0",
        expected="hello",
        msg="$trim should trim surrounding non-breaking spaces by default",
    ),
    # Unicode "Zs" category spaces.
    TrimTest(
        "default_en_space",
        input="\u2000hello\u2000",
        expected="hello",
        msg="$trim should trim surrounding en space (U+2000) by default",
    ),
    TrimTest(
        "default_em_space",
        input="\u2003hello\u2003",
        expected="hello",
        msg="$trim should trim surrounding em space (U+2003) by default",
    ),
    TrimTest(
        "default_thin_space",
        input="\u2009hello\u2009",
        expected="hello",
        msg="$trim should trim surrounding thin space (U+2009) by default",
    ),
    TrimTest(
        "default_hair_space",
        input="\u200ahello\u200a",
        expected="hello",
        msg="$trim should trim surrounding hair space (U+200A) by default",
    ),
    TrimTest(
        "default_ogham_space",
        input="\u1680hello\u1680",
        expected="hello",
        msg="$trim should trim surrounding ogham space (U+1680) by default",
    ),
    TrimTest(
        "default_em_quad",
        input="\u2001hello\u2001",
        expected="hello",
        msg="$trim should trim surrounding em quad (U+2001) by default",
    ),
    TrimTest(
        "default_en_space_2002",
        input="\u2002hello\u2002",
        expected="hello",
        msg="$trim should trim surrounding en space (U+2002) by default",
    ),
    TrimTest(
        "default_three_per_em",
        input="\u2004hello\u2004",
        expected="hello",
        msg="$trim should trim surrounding three-per-em space (U+2004) by default",
    ),
    TrimTest(
        "default_four_per_em",
        input="\u2005hello\u2005",
        expected="hello",
        msg="$trim should trim surrounding four-per-em space (U+2005) by default",
    ),
    TrimTest(
        "default_six_per_em",
        input="\u2006hello\u2006",
        expected="hello",
        msg="$trim should trim surrounding six-per-em space (U+2006) by default",
    ),
    TrimTest(
        "default_figure_space",
        input="\u2007hello\u2007",
        expected="hello",
        msg="$trim should trim surrounding figure space (U+2007) by default",
    ),
    TrimTest(
        "default_punctuation_space",
        input="\u2008hello\u2008",
        expected="hello",
        msg="$trim should trim surrounding punctuation space (U+2008) by default",
    ),
    # Multiple mixed whitespace characters.
    TrimTest(
        "default_mixed_ascii_whitespace",
        input=" \t\n\r\f\x0bhello\x0b\f\r\n\t ",
        expected="hello",
        msg="$trim should trim mixed ASCII whitespace from both ends",
    ),
    TrimTest(
        "default_mixed_unicode_whitespace",
        input="\u00a0\u2000\u2003hello\u2003\u2000\u00a0",
        expected="hello",
        msg="$trim should trim mixed Unicode whitespace from both ends",
    ),
    TrimTest(
        "default_mixed_ascii_and_unicode",
        input=" \t\u00a0\u2000hello\u2000\u00a0\t ",
        expected="hello",
        msg="$trim should trim mixed ASCII and Unicode whitespace from both ends",
    ),
    # Only leading whitespace.
    TrimTest(
        "default_leading_only",
        input="   hello",
        expected="hello",
        msg="$trim should trim leading-only whitespace",
    ),
    # Only trailing whitespace.
    TrimTest(
        "default_trailing_only",
        input="hello   ",
        expected="hello",
        msg="$trim should trim trailing-only whitespace",
    ),
    # Interior whitespace is preserved.
    TrimTest(
        "default_interior_preserved",
        input="  hello   world  ",
        expected="hello   world",
        msg="$trim should preserve interior whitespace",
    ),
    # All 20 default whitespace code points on both sides.
    TrimTest(
        "default_all_20_mixed",
        input=(
            "\x00\t\n\x0b\f\r \u00a0\u1680\u2000\u2001\u2002"
            "\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200ahello"
            "\u200a\u2009\u2008\u2007\u2006\u2005\u2004\u2003"
            "\u2002\u2001\u2000\u1680\u00a0 \r\f\x0b\n\t\x00"
        ),
        expected="hello",
        msg="$trim should trim all 20 default whitespace code points from both ends",
    ),
]


# Property [Default Trimming - exclusions]: characters not in the default whitespace set are
# preserved at both ends.
TRIM_DEFAULT_TRIM_EXCLUSION_TESTS: list[TrimTest] = [
    # Zero-width space (U+200B).
    TrimTest(
        "default_excl_zwsp",
        input="\u200bhello\u200b",
        expected="\u200bhello\u200b",
        msg="$trim should not trim zero-width space (U+200B) by default",
    ),
    # Line separator (U+2028).
    TrimTest(
        "default_excl_line_separator",
        input="\u2028hello\u2028",
        expected="\u2028hello\u2028",
        msg="$trim should not trim line separator (U+2028) by default",
    ),
    # Paragraph separator (U+2029).
    TrimTest(
        "default_excl_paragraph_separator",
        input="\u2029hello\u2029",
        expected="\u2029hello\u2029",
        msg="$trim should not trim paragraph separator (U+2029) by default",
    ),
    # Next line (U+0085).
    TrimTest(
        "default_excl_next_line",
        input="\u0085hello\u0085",
        expected="\u0085hello\u0085",
        msg="$trim should not trim next line (U+0085) by default",
    ),
    # Ideographic space (U+3000).
    TrimTest(
        "default_excl_ideographic_space",
        input="\u3000hello\u3000",
        expected="\u3000hello\u3000",
        msg="$trim should not trim ideographic space (U+3000) by default",
    ),
    # Narrow no-break space (U+202F).
    TrimTest(
        "default_excl_narrow_nbsp",
        input="\u202fhello\u202f",
        expected="\u202fhello\u202f",
        msg="$trim should not trim narrow no-break space (U+202F) by default",
    ),
    # Medium mathematical space (U+205F).
    TrimTest(
        "default_excl_medium_math_space",
        input="\u205fhello\u205f",
        expected="\u205fhello\u205f",
        msg="$trim should not trim medium mathematical space (U+205F) by default",
    ),
    # BOM / zero-width no-break space (U+FEFF).
    TrimTest(
        "default_excl_bom",
        input="\ufeffhello\ufeff",
        expected="\ufeffhello\ufeff",
        msg="$trim should not trim BOM / zero-width no-break space (U+FEFF) by default",
    ),
]


# Property [Edge Cases]: the operator produces correct results at input extremes: empty strings,
# fully trimmable strings, and large inputs.
TRIM_EDGE_TESTS: list[TrimTest] = [
    TrimTest(
        "edge_empty_default",
        input="",
        expected="",
        msg="$trim should return empty string for empty input with default chars",
    ),
    TrimTest(
        "edge_empty_custom",
        input="",
        chars="abc",
        expected="",
        msg="$trim should return empty string for empty input with custom chars",
    ),
    TrimTest(
        "edge_all_whitespace",
        input="   ",
        expected="",
        msg="$trim should return empty string when input is all whitespace",
    ),
    TrimTest(
        "edge_all_in_chars",
        input="aaabbb",
        chars="ab",
        expected="",
        msg="$trim should return empty string when all characters are in trim set",
    ),
    # Null byte in custom chars is not treated as a C-style string terminator.
    TrimTest(
        "edge_null_byte_custom",
        input="\x00\x00hello\x00\x00",
        chars="\x00",
        expected="hello",
        msg="$trim should trim null bytes without treating them as C-string terminators",
    ),
    # Control characters stop default trimming.
    TrimTest(
        "edge_control_char_stops_trim",
        input="\x01 hello \x01",
        expected="\x01 hello \x01",
        msg="$trim should not trim control character U+0001 by default",
    ),
    # Whitespace between content and control char is trimmed on the inner side.
    TrimTest(
        "edge_space_around_control_char",
        input=" \x01hello\x01 ",
        expected="\x01hello\x01",
        msg="$trim should trim surrounding spaces but stop at control characters",
    ),
]

TRIM_DEFAULT_TRIM_ALL_TESTS = (
    TRIM_DEFAULT_TRIM_TESTS + TRIM_DEFAULT_TRIM_EXCLUSION_TESTS + TRIM_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(TRIM_DEFAULT_TRIM_ALL_TESTS))
def test_trim_default_trim(collection, test_case: TrimTest):
    """Test $trim default trimming and edge cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
