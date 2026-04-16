from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.first.utils.first_common import (  # noqa: E501
    FirstTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Unicode and Encoding]: multi-byte UTF-8 strings, combining
# characters, ZWJ emoji, BOM, zero-width characters, null bytes, and control
# characters are all preserved without normalization when extracted as the first
# element.
FIRST_UNICODE_TESTS: list[FirstTest] = [
    # U+00E9: two-byte UTF-8 character (e with acute).
    FirstTest(
        "unicode_multibyte_two",
        value={"$literal": ["\u00e9", "x"]},
        expected="\u00e9",
        msg="$first should preserve two-byte UTF-8 character",
    ),
    # U+4E16: three-byte UTF-8 character (CJK ideograph).
    FirstTest(
        "unicode_multibyte_three",
        value={"$literal": ["\u4e16", "x"]},
        expected="\u4e16",
        msg="$first should preserve three-byte UTF-8 character",
    ),
    # U+1F600: four-byte UTF-8 emoji.
    FirstTest(
        "unicode_multibyte_four",
        value={"$literal": ["\U0001f600", "x"]},
        expected="\U0001f600",
        msg="$first should preserve four-byte UTF-8 emoji",
    ),
    # U+0065 + U+0301: combining character sequence (e + combining acute).
    FirstTest(
        "unicode_combining",
        value={"$literal": ["e\u0301", "x"]},
        expected="e\u0301",
        msg="$first should preserve combining character sequence",
    ),
    # ZWJ emoji sequence: family emoji U+1F468 U+200D U+1F469 U+200D U+1F467.
    FirstTest(
        "unicode_zwj_emoji",
        value={"$literal": ["\U0001f468\u200d\U0001f469\u200d\U0001f467", "x"]},
        expected="\U0001f468\u200d\U0001f469\u200d\U0001f467",
        msg="$first should preserve ZWJ emoji sequence",
    ),
    # U+FEFF: byte order mark.
    FirstTest(
        "unicode_bom",
        value={"$literal": ["\ufeff", "x"]},
        expected="\ufeff",
        msg="$first should preserve BOM character",
    ),
    # U+200B: zero-width space.
    FirstTest(
        "unicode_zero_width_space",
        value={"$literal": ["\u200b", "x"]},
        expected="\u200b",
        msg="$first should preserve zero-width space",
    ),
    # Embedded null byte.
    FirstTest(
        "unicode_null_byte",
        value={"$literal": ["a\x00b", "x"]},
        expected="a\x00b",
        msg="$first should preserve string with embedded null byte",
    ),
    # U+0001: control character.
    FirstTest(
        "unicode_control_char",
        value={"$literal": ["\x01", "x"]},
        expected="\x01",
        msg="$first should preserve control character",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(FIRST_UNICODE_TESTS))
def test_first_unicode(collection, test_case: FirstTest):
    """Test $first cases."""
    result = execute_expression(collection, {"$first": test_case.value})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
