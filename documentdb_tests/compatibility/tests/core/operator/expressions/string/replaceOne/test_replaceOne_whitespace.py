from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.replaceOne_common import (
    ReplaceOneTest,
    _expr,
)

# Property [Whitespace]: all ASCII and Unicode whitespace characters are matched
# exactly as literal content, with no equivalence between different whitespace types.
REPLACEONE_WHITESPACE_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "whitespace_space",
        input="hello world",
        find=" ",
        replacement="_",
        expected="hello_world",
        msg="$replaceOne whitespace space",
    ),
    ReplaceOneTest(
        "whitespace_tab",
        input="col1\tcol2",
        find="\t",
        replacement=" ",
        expected="col1 col2",
        msg="$replaceOne whitespace tab",
    ),
    ReplaceOneTest(
        "whitespace_newline",
        input="line1\nline2",
        find="\n",
        replacement=" ",
        expected="line1 line2",
        msg="$replaceOne whitespace newline",
    ),
    ReplaceOneTest(
        "whitespace_cr",
        input="line1\rline2",
        find="\r",
        replacement=" ",
        expected="line1 line2",
        msg="$replaceOne whitespace cr",
    ),
    # CRLF matched as a two-character unit.
    ReplaceOneTest(
        "whitespace_crlf_unit",
        input="line1\r\nline2",
        find="\r\n",
        replacement=" ",
        expected="line1 line2",
        msg="$replaceOne whitespace crlf unit",
    ),
    # Individual \r within CRLF.
    ReplaceOneTest(
        "whitespace_crlf_individual_cr",
        input="line1\r\nline2",
        find="\r",
        replacement="",
        expected="line1\nline2",
        msg="$replaceOne whitespace crlf individual cr",
    ),
    # Individual \n within CRLF.
    ReplaceOneTest(
        "whitespace_crlf_individual_lf",
        input="line1\r\nline2",
        find="\n",
        replacement="",
        expected="line1\rline2",
        msg="$replaceOne whitespace crlf individual lf",
    ),
    # NBSP (U+00A0) is not equivalent to ASCII space.
    ReplaceOneTest(
        "whitespace_nbsp_not_space",
        input="hello\u00a0world",
        find=" ",
        replacement="X",
        expected="hello\u00a0world",
        msg="$replaceOne whitespace nbsp not space",
    ),
    # NBSP matched exactly.
    ReplaceOneTest(
        "whitespace_nbsp_exact",
        input="hello\u00a0world",
        find="\u00a0",
        replacement="_",
        expected="hello_world",
        msg="$replaceOne whitespace nbsp exact",
    ),
    # En space (U+2000) is not equivalent to ASCII space.
    ReplaceOneTest(
        "whitespace_en_space_not_space",
        input="hello\u2000world",
        find=" ",
        replacement="X",
        expected="hello\u2000world",
        msg="$replaceOne whitespace en space not space",
    ),
    # En space matched exactly.
    ReplaceOneTest(
        "whitespace_en_space_exact",
        input="hello\u2000world",
        find="\u2000",
        replacement="_",
        expected="hello_world",
        msg="$replaceOne whitespace en space exact",
    ),
    # Em space (U+2003) is not equivalent to ASCII space.
    ReplaceOneTest(
        "whitespace_em_space_not_space",
        input="hello\u2003world",
        find=" ",
        replacement="X",
        expected="hello\u2003world",
        msg="$replaceOne whitespace em space not space",
    ),
    # Em space matched exactly.
    ReplaceOneTest(
        "whitespace_em_space_exact",
        input="hello\u2003world",
        find="\u2003",
        replacement="_",
        expected="hello_world",
        msg="$replaceOne whitespace em space exact",
    ),
]

# Property [Zero-Width and Invisible Characters]: BOM, ZWSP, ZWJ, LTR mark,
# and RTL mark are treated as regular code points and are findable and
# replaceable. Replacing a ZWJ within an emoji sequence breaks the sequence.
REPLACEONE_ZERO_WIDTH_TESTS: list[ReplaceOneTest] = [
    # BOM (U+FEFF) findable and replaceable.
    ReplaceOneTest(
        "zw_bom_find",
        input="hello\ufeffworld",
        find="\ufeff",
        replacement="X",
        expected="helloXworld",
        msg="$replaceOne zw bom find",
    ),
    # BOM as replacement.
    ReplaceOneTest(
        "zw_bom_replacement",
        input="helloXworld",
        find="X",
        replacement="\ufeff",
        expected="hello\ufeffworld",
        msg="$replaceOne zw bom replacement",
    ),
    # ZWSP (U+200B) findable and replaceable.
    ReplaceOneTest(
        "zw_zwsp_find",
        input="hello\u200bworld",
        find="\u200b",
        replacement="X",
        expected="helloXworld",
        msg="$replaceOne zw zwsp find",
    ),
    # ZWSP as replacement.
    ReplaceOneTest(
        "zw_zwsp_replacement",
        input="helloXworld",
        find="X",
        replacement="\u200b",
        expected="hello\u200bworld",
        msg="$replaceOne zw zwsp replacement",
    ),
    # ZWJ (U+200D) findable and replaceable.
    ReplaceOneTest(
        "zw_zwj_find",
        input="a\u200db",
        find="\u200d",
        replacement="X",
        expected="aXb",
        msg="$replaceOne zw zwj find",
    ),
    # LTR mark (U+200E) findable and replaceable.
    ReplaceOneTest(
        "zw_ltr_mark_find",
        input="hello\u200eworld",
        find="\u200e",
        replacement="X",
        expected="helloXworld",
        msg="$replaceOne zw ltr mark find",
    ),
    # RTL mark (U+200F) findable and replaceable.
    ReplaceOneTest(
        "zw_rtl_mark_find",
        input="hello\u200fworld",
        find="\u200f",
        replacement="X",
        expected="helloXworld",
        msg="$replaceOne zw rtl mark find",
    ),
    # ZWJ within emoji sequence: replacing ZWJ (U+200D) in 👨‍💻 (man + ZWJ +
    # laptop) breaks the sequence into separate codepoints.
    ReplaceOneTest(
        "zw_zwj_emoji_break",
        input="\U0001f468\u200d\U0001f4bb",
        find="\u200d",
        replacement="",
        expected="\U0001f468\U0001f4bb",
        msg="$replaceOne zw zwj emoji break",
    ),
]

REPLACEONE_WHITESPACE_ALL_TESTS = REPLACEONE_WHITESPACE_TESTS + REPLACEONE_ZERO_WIDTH_TESTS


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_WHITESPACE_ALL_TESTS))
def test_replaceone_whitespace_cases(collection, test_case: ReplaceOneTest):
    """Test $replaceOne whitespace and zero-width character cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
