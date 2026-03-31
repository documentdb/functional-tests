from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.rtrim.utils.rtrim_common import (
    RtrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Custom Chars]: when chars is provided, only those characters are trimmed from the
# trailing edge. Each character in chars is treated individually (not as a substring), and the
# order of characters in chars does not affect the result.
RTRIM_CUSTOM_CHARS_TESTS: list[RtrimTest] = [
    RtrimTest(
        "custom_single_char",
        input="helloaaa",
        chars="a",
        expected="hello",
        msg="$rtrim should trim trailing occurrences of a single custom char",
    ),
    RtrimTest(
        "custom_repeated_single",
        input="helloxxx",
        chars="x",
        expected="hello",
        msg="$rtrim should trim repeated trailing custom char",
    ),
    # Custom chars completely replaces the default whitespace set.
    RtrimTest(
        "custom_spaces_not_trimmed",
        input="helloxxx  ",
        chars="x",
        expected="helloxxx  ",
        msg="$rtrim should not trim spaces when custom chars replaces default set",
    ),
    RtrimTest(
        "custom_tabs_not_trimmed",
        input="helloxxx\t\t",
        chars="x",
        expected="helloxxx\t\t",
        msg="$rtrim should not trim tabs when custom chars replaces default set",
    ),
    # Duplicate characters in chars have no additional effect.
    RtrimTest(
        "custom_duplicate_chars",
        input="helloaaa",
        chars="aab",
        expected="hello",
        msg="$rtrim should ignore duplicate characters in chars",
    ),
    # Each character in chars is treated individually, not as a substring pattern.
    RtrimTest(
        "custom_individual_any_order",
        input="hellocba",
        chars="abc",
        expected="hello",
        msg="$rtrim should treat each char in chars individually, not as a substring",
    ),
    RtrimTest(
        "custom_individual_mixed_repeats",
        input="helloaabbcc",
        chars="abc",
        expected="hello",
        msg="$rtrim should trim mixed repeats of individual chars",
    ),
    # Characters not in chars are preserved.
    RtrimTest(
        "custom_no_match",
        input="hellox",
        chars="a",
        expected="hellox",
        msg="$rtrim should preserve trailing chars not in the trim set",
    ),
    # Order of characters in chars does not affect the result.
    RtrimTest(
        "custom_order_abc",
        input="hellobcaa",
        chars="abc",
        expected="hello",
        msg="$rtrim should produce same result regardless of chars order (abc)",
    ),
    RtrimTest(
        "custom_order_cba",
        input="hellobcaa",
        chars="cba",
        expected="hello",
        msg="$rtrim should produce same result regardless of chars order (cba)",
    ),
    RtrimTest(
        "custom_order_bac",
        input="hellobcaa",
        chars="bac",
        expected="hello",
        msg="$rtrim should produce same result regardless of chars order (bac)",
    ),
]


# Property [Directionality]: only trailing (right-side) characters are trimmed. Leading
# characters matching the trim set are preserved.
RTRIM_DIRECTIONALITY_TESTS: list[RtrimTest] = [
    RtrimTest(
        "dir_leading_spaces",
        input="   hello",
        expected="   hello",
        msg="$rtrim should preserve leading spaces",
    ),
    RtrimTest(
        "dir_trailing_trimmed_leading_kept",
        input="  hello  ",
        expected="  hello",
        msg="$rtrim should trim trailing spaces while preserving leading spaces",
    ),
    RtrimTest(
        "dir_custom_leading_kept",
        input="aaahelloaaa",
        chars="a",
        expected="aaahello",
        msg="$rtrim should trim trailing custom chars while preserving leading ones",
    ),
    RtrimTest(
        "dir_leading_tab_kept",
        input="\thello\t",
        expected="\thello",
        msg="$rtrim should trim trailing tab while preserving leading tab",
    ),
    # Last character not in trim set stops all trimming.
    RtrimTest(
        "dir_last_char_not_in_set",
        input="hxexlxlxo",
        chars="x",
        expected="hxexlxlxo",
        msg="$rtrim should not trim when last character is not in the trim set",
    ),
]

# Property [Whitespace Subset Chars]: when chars is a subset of whitespace characters, only
# those specific whitespace characters are trimmed; other whitespace is preserved.
RTRIM_WHITESPACE_SUBSET_TESTS: list[RtrimTest] = [
    RtrimTest(
        "subset_tab_only",
        input="\t hello \t",
        chars="\t",
        expected="\t hello ",
        msg="$rtrim with chars=tab should trim only trailing tabs, preserving spaces",
    ),
    RtrimTest(
        "subset_space_tab",
        input=" \t\nhello\n\t ",
        chars=" \t",
        expected=" \t\nhello\n",
        msg="$rtrim with chars=space+tab should preserve trailing newlines",
    ),
    RtrimTest(
        "subset_newline_only",
        input="hello \n\n",
        chars="\n",
        expected="hello ",
        msg="$rtrim with chars=newline should trim only trailing newlines, preserving spaces",
    ),
]

RTRIM_CUSTOM_CHARS_ALL_TESTS = (
    RTRIM_CUSTOM_CHARS_TESTS + RTRIM_DIRECTIONALITY_TESTS + RTRIM_WHITESPACE_SUBSET_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_CUSTOM_CHARS_ALL_TESTS))
def test_rtrim_custom_chars(collection, test_case: RtrimTest):
    """Test $rtrim custom chars and directionality."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
