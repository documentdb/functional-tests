"""
Integration tests for string expression operators interacting with each other.

These tests verify that composing multiple string operators produces correct
results. Individual operator edge cases are tested in each operator's own
folder; these tests focus on cross-operator interactions where behavioral
differences between engines are most likely to surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ExprTest(BaseTestCase):
    """Test case with an inline expression."""

    expr: Any = None


# Property [Concat-Split Round-Trip]: splitting a $concat-joined string recovers the original parts.
CONCAT_SPLIT_TESTS: list[ExprTest] = [
    ExprTest(
        "concat_split_simple",
        expr={"$split": [{"$concat": ["a", "-", "b", "-", "c"]}, "-"]},
        expected=["a", "b", "c"],
        msg="$split of $concat-joined parts should recover original parts",
    ),
    ExprTest(
        "concat_split_empty_parts",
        expr={"$split": [{"$concat": ["", "|", "a", "|", ""]}, "|"]},
        expected=["", "a", ""],
        msg="$split of $concat with empty parts should preserve empties",
    ),
    ExprTest(
        "concat_split_multibyte_delimiter",
        expr={"$split": [{"$concat": ["hello", "\u2192", "world"]}, "\u2192"]},
        expected=["hello", "world"],
        msg="$split of $concat with multi-byte delimiter should round-trip",
    ),
]

# Property [Case Chaining]: applying $toLower and $toUpper in sequence produces deterministic case.
CASE_CHAIN_TESTS: list[ExprTest] = [
    ExprTest(
        "lower_of_upper",
        expr={"$toLower": {"$toUpper": "Hello World"}},
        expected="hello world",
        msg="$toLower of $toUpper should produce lowercase",
    ),
    ExprTest(
        "upper_of_lower",
        expr={"$toUpper": {"$toLower": "Hello World"}},
        expected="HELLO WORLD",
        msg="$toUpper of $toLower should produce uppercase",
    ),
]

# Property [Trim-Concat Boundary]: $concat of $trim result does not reintroduce whitespace.
TRIM_CONCAT_TESTS: list[ExprTest] = [
    ExprTest(
        "trim_then_concat",
        expr={
            "$concat": [
                {"$trim": {"input": "  hello  "}},
                " ",
                {"$trim": {"input": "  world  "}},
            ]
        },
        expected="hello world",
        msg="$concat of trimmed strings should join without extra whitespace",
    ),
]

# Property [Find-Extract]: $substrCP at the position returned by $indexOfCP extracts the searched
# substring.
FIND_EXTRACT_TESTS: list[ExprTest] = [
    ExprTest(
        "find_extract_ascii",
        expr={
            "$substrCP": [
                "hello world",
                {"$indexOfCP": ["hello world", "world"]},
                {"$strLenCP": "world"},
            ]
        },
        expected="world",
        msg="$substrCP at $indexOfCP position should extract the searched substring",
    ),
    ExprTest(
        "find_extract_multibyte",
        expr={
            "$substrCP": [
                "caf\u00e9 latte",
                {"$indexOfCP": ["caf\u00e9 latte", "latte"]},
                {"$strLenCP": "latte"},
            ]
        },
        expected="latte",
        msg="$substrCP + $indexOfCP should work correctly with multi-byte prefix",
    ),
    ExprTest(
        "find_extract_emoji",
        expr={
            "$substrCP": [
                "hi \U0001f600 there",
                {"$indexOfCP": ["hi \U0001f600 there", "there"]},
                {"$strLenCP": "there"},
            ]
        },
        expected="there",
        msg="$substrCP + $indexOfCP should work correctly with 4-byte emoji prefix",
    ),
]

# Property [Replace-Case Ordering]: the order of $replaceAll and $toLower affects the result.
REPLACE_CASE_TESTS: list[ExprTest] = [
    ExprTest(
        "replace_then_lower",
        expr={
            "$toLower": {
                "$replaceAll": {
                    "input": "Hello World",
                    "find": "World",
                    "replacement": "EARTH",
                }
            }
        },
        expected="hello earth",
        msg="$toLower of $replaceAll should lowercase the replaced text",
    ),
    ExprTest(
        "lower_then_replace",
        expr={
            "$replaceAll": {
                "input": {"$toLower": "Hello World"},
                "find": "world",
                "replacement": "earth",
            }
        },
        expected="hello earth",
        msg="$replaceAll after $toLower should match against lowercase input",
    ),
]

# Property [Strcasecmp Case-Converted]: $strcasecmp returns 0 for $toLower vs $toUpper of the same
# ASCII string.
STRCASECMP_TESTS: list[ExprTest] = [
    ExprTest(
        "strcasecmp_lower_vs_upper",
        expr={"$strcasecmp": [{"$toLower": "Hello World"}, {"$toUpper": "Hello World"}]},
        expected=0,
        msg="$strcasecmp of $toLower and $toUpper of same string should be 0",
    ),
]


# Property [Length Divergence]: replacing ASCII with multi-byte chars preserves $strLenCP but
# increases $strLenBytes.
LENGTH_DIVERGENCE_TESTS: list[ExprTest] = [
    ExprTest(
        "replace_multibyte_cp_len",
        expr={
            "$strLenCP": {"$replaceAll": {"input": "hello", "find": "e", "replacement": "\u00e9"}}
        },
        expected=5,
        msg="$strLenCP should be unchanged after replacing ASCII with multi-byte char",
    ),
    ExprTest(
        "replace_multibyte_byte_len",
        expr={
            "$strLenBytes": {
                "$replaceAll": {"input": "hello", "find": "e", "replacement": "\u00e9"}
            }
        },
        expected=6,
        msg="$strLenBytes should increase after replacing ASCII with multi-byte char",
    ),
]

# Property [Trim Equivalence]: $trim(input, chars) == $ltrim($rtrim(input, chars), chars).
TRIM_EQUIVALENCE_TESTS: list[ExprTest] = [
    ExprTest(
        "trim_eq_ltrim_rtrim_default",
        expr={
            "$eq": [
                {"$trim": {"input": "  hello  "}},
                {"$ltrim": {"input": {"$rtrim": {"input": "  hello  "}}}},
            ]
        },
        expected=True,
        msg="$trim should equal $ltrim($rtrim(x)) with default whitespace",
    ),
    ExprTest(
        "trim_eq_ltrim_rtrim_custom",
        expr={
            "$eq": [
                {"$trim": {"input": "aaahelloaaa", "chars": "a"}},
                {
                    "$ltrim": {
                        "input": {"$rtrim": {"input": "aaahelloaaa", "chars": "a"}},
                        "chars": "a",
                    }
                },
            ]
        },
        expected=True,
        msg="$trim should equal $ltrim($rtrim(x)) with custom chars",
    ),
    ExprTest(
        "trim_eq_ltrim_rtrim_mixed_ws",
        expr={
            "$eq": [
                {"$trim": {"input": " \t\nhello\n\t "}},
                {"$ltrim": {"input": {"$rtrim": {"input": " \t\nhello\n\t "}}}},
            ]
        },
        expected=True,
        msg="$trim should equal $ltrim($rtrim(x)) with mixed whitespace",
    ),
]

# Property [Concat Length From Expressions]: $strLenCP of $concat equals expected length when inputs
# are expression results.
CONCAT_LENGTH_TESTS: list[ExprTest] = [
    ExprTest(
        "concat_length_from_expressions",
        expr={
            "$strLenCP": {
                "$concat": [
                    {"$toUpper": "caf\u00e9"},
                    {"$replaceAll": {"input": "hello", "find": "l", "replacement": "LL"}},
                ]
            }
        },
        expected=11,
        msg="$strLenCP of $concat of expression results should equal expected length",
    ),
]

STRING_COMBINATION_TESTS = (
    CONCAT_SPLIT_TESTS
    + CASE_CHAIN_TESTS
    + TRIM_CONCAT_TESTS
    + FIND_EXTRACT_TESTS
    + REPLACE_CASE_TESTS
    + STRCASECMP_TESTS
    + LENGTH_DIVERGENCE_TESTS
    + CONCAT_LENGTH_TESTS
    + TRIM_EQUIVALENCE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(STRING_COMBINATION_TESTS))
def test_string_combination(collection, test_case: ExprTest):
    """Test string operator combinations."""
    result = execute_expression(collection, test_case.expr)
    assertSuccess(result, [{"result": test_case.expected}], msg=test_case.msg)
