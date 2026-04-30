from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.strLenCP_common import (
    StrLenCPTest,
    _expr,
)

# Property [Core Behavior]: returns the number of UTF-8 code points in the input string.
STRLENCP_CORE_TESTS: list[StrLenCPTest] = [
    StrLenCPTest("core_empty", value="", expected=0, msg="$strLenCP of empty string should be 0"),
    StrLenCPTest("core_space", value=" ", expected=1, msg="$strLenCP of space should be 1"),
    StrLenCPTest(
        "core_multiple_spaces", value="   ", expected=3, msg="$strLenCP of three spaces should be 3"
    ),
    StrLenCPTest(
        "core_ascii_word",
        value="hello",
        expected=5,
        msg="$strLenCP of ASCII word should equal character count",
    ),
    StrLenCPTest("core_newline", value="\n", expected=1, msg="$strLenCP of newline should be 1"),
    StrLenCPTest("core_tab", value="\t", expected=1, msg="$strLenCP of tab should be 1"),
    StrLenCPTest("core_cr", value="\r", expected=1, msg="$strLenCP of carriage return should be 1"),
    StrLenCPTest(
        "core_null_byte", value="\x00", expected=1, msg="$strLenCP of null byte should be 1"
    ),
    StrLenCPTest("core_crlf", value="\r\n", expected=2, msg="$strLenCP of CRLF should be 2"),
    # 2-byte UTF-8: Latin extended, Greek.
    StrLenCPTest(
        "core_2byte_e_acute",
        value="é",
        expected=1,
        msg="$strLenCP of 2-byte é should be 1 code point",
    ),
    StrLenCPTest(
        "core_2byte_n_tilde",
        value="ñ",
        expected=1,
        msg="$strLenCP of 2-byte ñ should be 1 code point",
    ),
    StrLenCPTest(
        "core_2byte_greek",
        value="λ",
        expected=1,
        msg="$strLenCP of 2-byte Greek lambda should be 1 code point",
    ),
    # 3-byte UTF-8: CJK, Euro sign, BOM, ZWJ.
    StrLenCPTest(
        "core_3byte_cjk",
        value="寿",
        expected=1,
        msg="$strLenCP of 3-byte CJK character should be 1 code point",
    ),
    StrLenCPTest(
        "core_3byte_euro",
        value="€",
        expected=1,
        msg="$strLenCP of 3-byte Euro sign should be 1 code point",
    ),
    StrLenCPTest(
        "core_3byte_bom",
        value="\ufeff",
        expected=1,
        msg="$strLenCP of 3-byte BOM should be 1 code point",
    ),
    StrLenCPTest(
        "core_3byte_zwj",
        value="\u200d",
        expected=1,
        msg="$strLenCP of 3-byte ZWJ should be 1 code point",
    ),
    StrLenCPTest(
        "core_3byte_zwsp",
        value="\u200b",
        expected=1,
        msg="$strLenCP of 3-byte zero-width space should be 1 code point",
    ),
    # 4-byte UTF-8: emoji, math symbols.
    StrLenCPTest(
        "core_4byte_emoji",
        value="😀",
        expected=1,
        msg="$strLenCP of 4-byte emoji should be 1 code point",
    ),
    StrLenCPTest(
        "core_4byte_math",
        value="𝜋",
        expected=1,
        msg="$strLenCP of 4-byte math symbol should be 1 code point",
    ),
    StrLenCPTest(
        "core_4byte_party",
        value="🎉",
        expected=1,
        msg="$strLenCP of 4-byte party emoji should be 1 code point",
    ),
    # Mixed byte widths.
    StrLenCPTest(
        "core_mixed_all_widths",
        value="aé€😀",
        expected=4,
        msg="$strLenCP should count each character as 1 code point regardless of byte width",
    ),
    StrLenCPTest(
        "core_mixed_latin",
        value="cafétéria",
        expected=9,
        msg="$strLenCP should count mixed ASCII and accented chars as individual code points",
    ),
    StrLenCPTest(
        "core_mixed_spanish",
        value="jalapeño",
        expected=8,
        msg="$strLenCP should count ñ as 1 code point",
    ),
    # Precomposed U+00E9 (1 code point) vs decomposed U+0065 + U+0301 (2 code points).
    StrLenCPTest(
        "core_precomposed",
        value="\u00e9",
        expected=1,
        msg="$strLenCP of precomposed é should be 1 code point",
    ),
    StrLenCPTest(
        "core_decomposed",
        value="e\u0301",
        expected=2,
        msg="$strLenCP of decomposed é (e + combining accent) should be 2 code points",
    ),
    # ZWJ emoji sequence: 3 emoji + 2 ZWJ (U+200D) = 5 code points.
    StrLenCPTest(
        "core_zwj_emoji",
        value="👨\u200d👩\u200d👧",
        expected=5,
        msg="$strLenCP of ZWJ emoji sequence should count each emoji and joiner separately",
    ),
    # Mixed scripts.
    StrLenCPTest(
        "core_accent_word",
        value="café",
        expected=4,
        msg="$strLenCP of 'café' should be 4 code points",
    ),
    StrLenCPTest(
        "core_cjk_word", value="寿司", expected=2, msg="$strLenCP of two CJK characters should be 2"
    ),
    StrLenCPTest(
        "core_mixed_scripts",
        value="hello 世界",
        expected=8,
        msg="$strLenCP should count ASCII and CJK as 1 code point each",
    ),
]


# Property [Encoding and Character Handling]: whitespace variants, control characters, directional
# markers, encoding boundary characters, and locale-sensitive letters are each counted as exactly 1
# code point.
STRLENCP_ENCODING_TESTS: list[StrLenCPTest] = [
    # Whitespace variants.
    StrLenCPTest(
        "encoding_nbsp",
        value="\u00a0",
        expected=1,
        msg="$strLenCP of non-breaking space should be 1",
    ),
    StrLenCPTest(
        "encoding_en_space", value="\u2000", expected=1, msg="$strLenCP of en space should be 1"
    ),
    StrLenCPTest(
        "encoding_em_space", value="\u2003", expected=1, msg="$strLenCP of em space should be 1"
    ),
    # Control characters.
    StrLenCPTest(
        "encoding_control_soh",
        value="\x01",
        expected=1,
        msg="$strLenCP of SOH control character should be 1",
    ),
    StrLenCPTest(
        "encoding_control_us",
        value="\x1f",
        expected=1,
        msg="$strLenCP of US control character should be 1",
    ),
    # Directional markers.
    StrLenCPTest(
        "encoding_ltr_mark",
        value="\u200e",
        expected=1,
        msg="$strLenCP of left-to-right mark should be 1",
    ),
    StrLenCPTest(
        "encoding_rtl_mark",
        value="\u200f",
        expected=1,
        msg="$strLenCP of right-to-left mark should be 1",
    ),
    # UTF-8 encoding boundary characters.
    StrLenCPTest(
        "encoding_boundary_d7ff",
        value="\ud7ff",
        expected=1,
        msg="$strLenCP of U+D7FF (last pre-surrogate) should be 1",
    ),
    StrLenCPTest(
        "encoding_boundary_e000",
        value="\ue000",
        expected=1,
        msg="$strLenCP of U+E000 (first PUA) should be 1",
    ),
    StrLenCPTest(
        "encoding_boundary_ffff",
        value="\uffff",
        expected=1,
        msg="$strLenCP of U+FFFF (last BMP) should be 1",
    ),
    StrLenCPTest(
        "encoding_boundary_10000",
        value="\U00010000",
        expected=1,
        msg="$strLenCP of U+10000 (first supplementary) should be 1",
    ),
    StrLenCPTest(
        "encoding_boundary_10ffff",
        value="\U0010ffff",
        expected=1,
        msg="$strLenCP of U+10FFFF (last valid codepoint) should be 1",
    ),
    # Deseret script.
    StrLenCPTest(
        "encoding_deseret",
        value="\U00010400",
        expected=1,
        msg="$strLenCP of Deseret character should be 1",
    ),
    # Locale-sensitive letters.
    StrLenCPTest(
        "encoding_sharp_s", value="ß", expected=1, msg="$strLenCP of German sharp s should be 1"
    ),
    StrLenCPTest(
        "encoding_fi_ligature",
        value="\ufb01",
        expected=1,
        msg="$strLenCP of fi ligature should be 1",
    ),
    StrLenCPTest(
        "encoding_dotless_i",
        value="\u0131",
        expected=1,
        msg="$strLenCP of Turkish dotless i should be 1",
    ),
]

# Property [Embedded Null Bytes]: null bytes in various positions do not cause early string
# termination.
STRLENCP_NULL_BYTE_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "null_byte_at_start",
        value="\x00xyz",
        expected=4,
        msg="$strLenCP should not terminate early on leading null byte",
    ),
    StrLenCPTest(
        "null_byte_at_end",
        value="xyz\x00",
        expected=4,
        msg="$strLenCP should not terminate early on trailing null byte",
    ),
    StrLenCPTest(
        "null_byte_multiple",
        value="a\x00b\x00c\x00",
        expected=6,
        msg="$strLenCP should count all code points with interleaved null bytes",
    ),
    StrLenCPTest(
        "null_byte_with_multibyte",
        value="寿\x00司",
        expected=3,
        msg="$strLenCP should count all code points with null byte between multibyte chars",
    ),
]

STRLENCP_CODE_POINT_TESTS = STRLENCP_CORE_TESTS + STRLENCP_ENCODING_TESTS + STRLENCP_NULL_BYTE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(STRLENCP_CODE_POINT_TESTS))
def test_strlencp_cases(collection, test_case: StrLenCPTest):
    """Test $strLenCP cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
