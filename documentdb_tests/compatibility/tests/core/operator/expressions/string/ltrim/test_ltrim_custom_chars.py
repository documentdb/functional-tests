from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.ltrim.utils.ltrim_common import (
    LtrimTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Custom Chars]: when chars is provided, only those characters are trimmed from the
# leading edge. Each character in chars is treated individually (not as a substring), and the
# order of characters in chars does not affect the result.
LTRIM_CUSTOM_CHARS_TESTS: list[LtrimTest] = [
    LtrimTest(
        "custom_single_char",
        input="aaahello",
        chars="a",
        expected="hello",
        msg="$ltrim should trim leading occurrences of a single custom char",
    ),
    LtrimTest(
        "custom_repeated_single",
        input="xxxhello",
        chars="x",
        expected="hello",
        msg="$ltrim should trim repeated leading custom char",
    ),
    # Custom chars completely replaces the default whitespace set.
    LtrimTest(
        "custom_spaces_not_trimmed",
        input="  xxxhello",
        chars="x",
        expected="  xxxhello",
        msg="$ltrim should not trim spaces when custom chars replaces default set",
    ),
    LtrimTest(
        "custom_tabs_not_trimmed",
        input="\t\txxxhello",
        chars="x",
        expected="\t\txxxhello",
        msg="$ltrim should not trim tabs when custom chars replaces default set",
    ),
    # Duplicate characters in chars have no additional effect.
    LtrimTest(
        "custom_duplicate_chars",
        input="aaahello",
        chars="aab",
        expected="hello",
        msg="$ltrim should ignore duplicate characters in chars",
    ),
    # Each character in chars is treated individually, not as a substring pattern.
    LtrimTest(
        "custom_individual_any_order",
        input="cbahello",
        chars="abc",
        expected="hello",
        msg="$ltrim should treat each char in chars individually, not as a substring",
    ),
    LtrimTest(
        "custom_individual_mixed_repeats",
        input="aabbcchello",
        chars="abc",
        expected="hello",
        msg="$ltrim should trim mixed repeats of individual chars",
    ),
    # Characters not in chars are preserved.
    LtrimTest(
        "custom_no_match",
        input="xhello",
        chars="a",
        expected="xhello",
        msg="$ltrim should preserve leading chars not in the trim set",
    ),
    # Order of characters in chars does not affect the result.
    LtrimTest(
        "custom_order_abc",
        input="bcaahello",
        chars="abc",
        expected="hello",
        msg="$ltrim should produce same result regardless of chars order (abc)",
    ),
    LtrimTest(
        "custom_order_cba",
        input="bcaahello",
        chars="cba",
        expected="hello",
        msg="$ltrim should produce same result regardless of chars order (cba)",
    ),
    LtrimTest(
        "custom_order_bac",
        input="bcaahello",
        chars="bac",
        expected="hello",
        msg="$ltrim should produce same result regardless of chars order (bac)",
    ),
]


# Property [Directionality]: only leading (left-side) characters are trimmed. Trailing characters
# matching the trim set are preserved.
LTRIM_DIRECTIONALITY_TESTS: list[LtrimTest] = [
    LtrimTest(
        "dir_trailing_spaces",
        input="hello   ",
        expected="hello   ",
        msg="$ltrim should preserve trailing spaces",
    ),
    LtrimTest(
        "dir_leading_trimmed_trailing_kept",
        input="  hello  ",
        expected="hello  ",
        msg="$ltrim should trim leading spaces while preserving trailing spaces",
    ),
    LtrimTest(
        "dir_custom_trailing_kept",
        input="aaahelloaaa",
        chars="a",
        expected="helloaaa",
        msg="$ltrim should trim leading custom chars while preserving trailing ones",
    ),
    LtrimTest(
        "dir_trailing_tab_kept",
        input="\thello\t",
        expected="hello\t",
        msg="$ltrim should trim leading tab while preserving trailing tab",
    ),
    # First character not in trim set stops all trimming.
    LtrimTest(
        "dir_first_char_not_in_set",
        input="hxexlxlxo",
        chars="x",
        expected="hxexlxlxo",
        msg="$ltrim should not trim when first character is not in the trim set",
    ),
]

# Property [Whitespace Subset Chars]: when chars is a subset of whitespace characters, only
# those specific whitespace characters are trimmed; other whitespace is preserved.
LTRIM_WHITESPACE_SUBSET_TESTS: list[LtrimTest] = [
    LtrimTest(
        "subset_tab_only",
        input="\t hello \t",
        chars="\t",
        expected=" hello \t",
        msg="$ltrim with chars=tab should trim only leading tabs, preserving spaces",
    ),
    LtrimTest(
        "subset_space_tab",
        input=" \t\nhello\n\t ",
        chars=" \t",
        expected="\nhello\n\t ",
        msg="$ltrim with chars=space+tab should preserve leading newlines",
    ),
    LtrimTest(
        "subset_newline_only",
        input="\n\n hello",
        chars="\n",
        expected=" hello",
        msg="$ltrim with chars=newline should trim only leading newlines, preserving spaces",
    ),
]

LTRIM_CUSTOM_CHARS_ALL_TESTS = (
    LTRIM_CUSTOM_CHARS_TESTS + LTRIM_DIRECTIONALITY_TESTS + LTRIM_WHITESPACE_SUBSET_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_CUSTOM_CHARS_ALL_TESTS))
def test_ltrim_custom_chars(collection, test_case: LtrimTest):
    """Test $ltrim custom chars and directionality cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
