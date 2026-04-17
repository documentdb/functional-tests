from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.last.utils.last_common import (  # noqa: E501
    LastTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Unicode and Encoding]: multi-byte UTF-8 strings, combining
# characters, ZWJ emoji, BOM, zero-width characters, null bytes, and control
# characters are all preserved without normalization when extracted as the last
# element.
LAST_UNICODE_TESTS: list[LastTest] = [
    # U+00E9: two-byte UTF-8 character (e with acute).
    LastTest(
        "unicode_multibyte_two",
        value={"$literal": ["x", "\u00e9"]},
        expected="\u00e9",
        msg="$last should preserve two-byte UTF-8 character",
    ),
    # U+4E16: three-byte UTF-8 character (CJK ideograph).
    LastTest(
        "unicode_multibyte_three",
        value={"$literal": ["x", "\u4e16"]},
        expected="\u4e16",
        msg="$last should preserve three-byte UTF-8 character",
    ),
    # U+1F600: four-byte UTF-8 emoji.
    LastTest(
        "unicode_multibyte_four",
        value={"$literal": ["x", "\U0001f600"]},
        expected="\U0001f600",
        msg="$last should preserve four-byte UTF-8 emoji",
    ),
    # U+0065 + U+0301: combining character sequence (e + combining acute).
    LastTest(
        "unicode_combining",
        value={"$literal": ["x", "e\u0301"]},
        expected="e\u0301",
        msg="$last should preserve combining character sequence",
    ),
    # ZWJ emoji sequence: family emoji U+1F468 U+200D U+1F469 U+200D U+1F467.
    LastTest(
        "unicode_zwj_emoji",
        value={"$literal": ["x", "\U0001f468\u200d\U0001f469\u200d\U0001f467"]},
        expected="\U0001f468\u200d\U0001f469\u200d\U0001f467",
        msg="$last should preserve ZWJ emoji sequence",
    ),
    # U+FEFF: byte order mark.
    LastTest(
        "unicode_bom",
        value={"$literal": ["x", "\ufeff"]},
        expected="\ufeff",
        msg="$last should preserve BOM character",
    ),
    # U+200B: zero-width space.
    LastTest(
        "unicode_zero_width_space",
        value={"$literal": ["x", "\u200b"]},
        expected="\u200b",
        msg="$last should preserve zero-width space",
    ),
    # Embedded null byte.
    LastTest(
        "unicode_null_byte",
        value={"$literal": ["x", "a\x00b"]},
        expected="a\x00b",
        msg="$last should preserve string with embedded null byte",
    ),
    # U+0001: control character.
    LastTest(
        "unicode_control_char",
        value={"$literal": ["x", "\x01"]},
        expected="\x01",
        msg="$last should preserve control character",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LAST_UNICODE_TESTS))
def test_last_unicode(collection, test_case: LastTest):
    """Test $last cases."""
    result = execute_expression(collection, {"$last": test_case.value})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
