from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.strLenBytes_common import (
    StrLenBytesTest,
    _expr,
)

# Property [Core Behavior]: returns the number of UTF-8 encoded bytes in the input string.
STRLENBYTES_CORE_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "core_empty", value="", expected=0, msg="$strLenBytes of empty string should be 0"
    ),
    StrLenBytesTest("core_space", value=" ", expected=1, msg="$strLenBytes of space should be 1"),
    StrLenBytesTest(
        "core_multiple_space",
        value="   ",
        expected=3,
        msg="$strLenBytes of three spaces should be 3",
    ),
    StrLenBytesTest(
        "core_ascii_word",
        value="hello",
        expected=5,
        msg="$strLenBytes of ASCII word should equal character count",
    ),
    StrLenBytesTest(
        "core_newline", value="\n", expected=1, msg="$strLenBytes of newline should be 1"
    ),
    StrLenBytesTest("core_tab", value="\t", expected=1, msg="$strLenBytes of tab should be 1"),
    StrLenBytesTest(
        "core_cr", value="\r", expected=1, msg="$strLenBytes of carriage return should be 1"
    ),
    StrLenBytesTest(
        "core_null_byte", value="\x00", expected=1, msg="$strLenBytes of null byte should be 1"
    ),
    StrLenBytesTest("core_crlf", value="\r\n", expected=2, msg="$strLenBytes of CRLF should be 2"),
    # 2-byte: Latin extended, Greek.
    StrLenBytesTest(
        "core_2byte_e_acute", value="é", expected=2, msg="$strLenBytes of 2-byte é should be 2"
    ),
    StrLenBytesTest(
        "core_2byte_n_tilde", value="ñ", expected=2, msg="$strLenBytes of 2-byte ñ should be 2"
    ),
    StrLenBytesTest(
        "core_2byte_greek",
        value="λ",
        expected=2,
        msg="$strLenBytes of 2-byte Greek lambda should be 2",
    ),
    # 3-byte: CJK, Euro sign, BOM, ZWJ.
    StrLenBytesTest(
        "core_3byte_cjk",
        value="寿",
        expected=3,
        msg="$strLenBytes of 3-byte CJK character should be 3",
    ),
    StrLenBytesTest(
        "core_3byte_euro", value="€", expected=3, msg="$strLenBytes of 3-byte Euro sign should be 3"
    ),
    StrLenBytesTest(
        "core_3byte_bom", value="\ufeff", expected=3, msg="$strLenBytes of 3-byte BOM should be 3"
    ),
    StrLenBytesTest(
        "core_3byte_zwj", value="\u200d", expected=3, msg="$strLenBytes of 3-byte ZWJ should be 3"
    ),
    # 4-byte: emoji, math symbols.
    StrLenBytesTest(
        "core_4byte_emoji", value="😀", expected=4, msg="$strLenBytes of 4-byte emoji should be 4"
    ),
    StrLenBytesTest(
        "core_4byte_math",
        value="𝜋",
        expected=4,
        msg="$strLenBytes of 4-byte math symbol should be 4",
    ),
    StrLenBytesTest(
        "core_4byte_party",
        value="🎉",
        expected=4,
        msg="$strLenBytes of 4-byte party emoji should be 4",
    ),
    # Mixed byte widths.
    StrLenBytesTest(
        "core_mixed_all_widths",
        value="aé€😀",
        expected=10,
        msg="$strLenBytes should sum bytes across 1/2/3/4-byte characters",
    ),
    StrLenBytesTest(
        "core_mixed_latin",
        value="cafétéria",
        expected=11,
        msg="$strLenBytes should count mixed ASCII and 2-byte chars correctly",
    ),
    StrLenBytesTest(
        "core_mixed_spanish",
        value="jalapeño",
        expected=9,
        msg="$strLenBytes should count ñ as 2 bytes in mixed string",
    ),
    # Precomposed U+00E9 (2 bytes) vs decomposed U+0065 + U+0301 (1 + 2 = 3 bytes).
    StrLenBytesTest(
        "core_precomposed",
        value="\u00e9",
        expected=2,
        msg="$strLenBytes of precomposed é should be 2 bytes",
    ),
    StrLenBytesTest(
        "core_decomposed",
        value="e\u0301",
        expected=3,
        msg="$strLenBytes of decomposed é (e + combining accent) should be 3 bytes",
    ),
    # ZWJ emoji sequence: 3 emoji (4 bytes each) + 2 ZWJ (3 bytes each) = 18.
    StrLenBytesTest(
        "core_zwj_emoji",
        value="👨\u200d👩\u200d👧",
        expected=18,
        msg="$strLenBytes of ZWJ emoji sequence should count all bytes including joiners",
    ),
    # Mixed scripts.
    StrLenBytesTest(
        "core_accent_word",
        value="café",
        expected=5,
        msg="$strLenBytes of 'café' should be 5 (3 ASCII + 1 two-byte)",
    ),
    StrLenBytesTest(
        "core_cjk_word",
        value="寿司",
        expected=6,
        msg="$strLenBytes of two CJK characters should be 6",
    ),
    StrLenBytesTest(
        "core_mixed_scripts",
        value="hello 世界",
        expected=12,
        msg="$strLenBytes should sum ASCII and CJK byte widths",
    ),
]

# Property [Encoding and Character Handling]: characters at UTF-8 encoding boundaries and special
# Unicode categories produce correct byte counts.
STRLENBYTES_ENCODING_TESTS: list[StrLenBytesTest] = [
    # U+00A0 non-breaking space (2 bytes).
    StrLenBytesTest(
        "encoding_nbsp",
        value="\u00a0",
        expected=2,
        msg="$strLenBytes of non-breaking space should be 2",
    ),
    # U+2000 en space (3 bytes).
    StrLenBytesTest(
        "encoding_en_space", value="\u2000", expected=3, msg="$strLenBytes of en space should be 3"
    ),
    # U+2003 em space (3 bytes).
    StrLenBytesTest(
        "encoding_em_space", value="\u2003", expected=3, msg="$strLenBytes of em space should be 3"
    ),
    # U+0001 SOH control character (1 byte).
    StrLenBytesTest(
        "encoding_control_soh",
        value="\x01",
        expected=1,
        msg="$strLenBytes of SOH control character should be 1",
    ),
    # U+001F US control character (1 byte).
    StrLenBytesTest(
        "encoding_control_us",
        value="\x1f",
        expected=1,
        msg="$strLenBytes of US control character should be 1",
    ),
    # U+200B zero-width space (3 bytes).
    StrLenBytesTest(
        "encoding_zero_width_space",
        value="\u200b",
        expected=3,
        msg="$strLenBytes of zero-width space should be 3",
    ),
    # U+200E left-to-right mark (3 bytes).
    StrLenBytesTest(
        "encoding_ltr_mark",
        value="\u200e",
        expected=3,
        msg="$strLenBytes of left-to-right mark should be 3",
    ),
    # U+200F right-to-left mark (3 bytes).
    StrLenBytesTest(
        "encoding_rtl_mark",
        value="\u200f",
        expected=3,
        msg="$strLenBytes of right-to-left mark should be 3",
    ),
    # U+D7FF: last codepoint before surrogates (3 bytes).
    StrLenBytesTest(
        "encoding_boundary_d7ff",
        value="\ud7ff",
        expected=3,
        msg="$strLenBytes of U+D7FF (last pre-surrogate) should be 3",
    ),
    # U+E000: first private use area codepoint (3 bytes).
    StrLenBytesTest(
        "encoding_boundary_e000",
        value="\ue000",
        expected=3,
        msg="$strLenBytes of U+E000 (first PUA) should be 3",
    ),
    # U+FFFF: last BMP codepoint (3 bytes).
    StrLenBytesTest(
        "encoding_boundary_ffff",
        value="\uffff",
        expected=3,
        msg="$strLenBytes of U+FFFF (last BMP) should be 3",
    ),
    # U+10000: first supplementary plane codepoint (4 bytes).
    StrLenBytesTest(
        "encoding_boundary_10000",
        value="\U00010000",
        expected=4,
        msg="$strLenBytes of U+10000 (first supplementary) should be 4",
    ),
    # U+10FFFF: last valid Unicode codepoint (4 bytes).
    StrLenBytesTest(
        "encoding_boundary_10ffff",
        value="\U0010ffff",
        expected=4,
        msg="$strLenBytes of U+10FFFF (last valid codepoint) should be 4",
    ),
    # U+10400 Deseret capital long I (4 bytes).
    StrLenBytesTest(
        "encoding_deseret",
        value="\U00010400",
        expected=4,
        msg="$strLenBytes of Deseret character should be 4",
    ),
    # German sharp s (2 bytes).
    StrLenBytesTest(
        "encoding_sharp_s", value="ß", expected=2, msg="$strLenBytes of German sharp s should be 2"
    ),
    # U+FB01 fi ligature (3 bytes).
    StrLenBytesTest(
        "encoding_fi_ligature",
        value="\ufb01",
        expected=3,
        msg="$strLenBytes of fi ligature should be 3",
    ),
    # U+0131 Turkish dotless i (2 bytes).
    StrLenBytesTest(
        "encoding_dotless_i",
        value="\u0131",
        expected=2,
        msg="$strLenBytes of Turkish dotless i should be 2",
    ),
]


# Property [Embedded Null Bytes]: null bytes in various positions do not cause early string
# termination.
STRLENBYTES_NULL_BYTE_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "null_byte_at_start",
        value="\x00xyz",
        expected=4,
        msg="$strLenBytes should not terminate early on leading null byte",
    ),
    StrLenBytesTest(
        "null_byte_at_end",
        value="xyz\x00",
        expected=4,
        msg="$strLenBytes should not terminate early on trailing null byte",
    ),
    StrLenBytesTest(
        "null_byte_multiple",
        value="a\x00b\x00c\x00",
        expected=6,
        msg="$strLenBytes should count all bytes with interleaved null bytes",
    ),
    StrLenBytesTest(
        "null_byte_with_multibyte",
        value="寿\x00司",
        expected=7,
        msg="$strLenBytes should count all bytes with null byte between multibyte chars",
    ),
]

STRLENBYTES_BYTE_COUNT_TESTS = (
    STRLENBYTES_CORE_TESTS + STRLENBYTES_ENCODING_TESTS + STRLENBYTES_NULL_BYTE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(STRLENBYTES_BYTE_COUNT_TESTS))
def test_strlenbytes_cases(collection, test_case: StrLenBytesTest):
    """Test $strLenBytes byte count cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
