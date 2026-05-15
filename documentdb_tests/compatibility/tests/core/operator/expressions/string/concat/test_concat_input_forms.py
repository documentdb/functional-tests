from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.concat_common import (
    ConcatTest,
)

# Property [Arity]: $concat works with varying argument counts.
CONCAT_ARITY_TESTS: list[ConcatTest] = [
    ConcatTest(
        "arity_single",
        args=["solo"],
        expected="solo",
        msg="$concat should accept a single argument",
    ),
    ConcatTest(
        "arity_two",
        args=["hello", "world"],
        expected="helloworld",
        msg="$concat should accept two arguments",
    ),
]

# Empty array is inline-only since stored modes need at least one arg.
CONCAT_ARITY_EMPTY: list[ConcatTest] = [
    ConcatTest(
        "arity_empty_array",
        args=[],
        expected="",
        msg="$concat of empty array should return empty string",
    ),
]

# Property [Large Arity]: $concat accepts at least 1,000 arguments and produces the expected result.
# 1,000 is an arbitrary high count chosen to be well above typical usage.
CONCAT_LARGE_ARITY_TESTS: list[ConcatTest] = [
    ConcatTest(
        "large_arity_1000",
        args=[str(i % 10) for i in range(1_000)],
        expected="".join(str(i % 10) for i in range(1_000)),
        msg="$concat should accept 1000 arguments",
    ),
]

# Property [Expression Arguments]: $concat accepts any expression that resolves to a string.
CONCAT_EXPR_TESTS: list[ConcatTest] = [
    ConcatTest(
        "expr_toupper",
        args=[{"$toUpper": "hello"}],
        expected="HELLO",
        msg="$concat should accept $toUpper expression as argument",
    ),
    ConcatTest(
        "expr_tolower",
        args=[{"$toLower": "WORLD"}],
        expected="world",
        msg="$concat should accept $toLower expression as argument",
    ),
    ConcatTest(
        "expr_two_expressions",
        args=[{"$toUpper": "hello"}, {"$toLower": "WORLD"}],
        expected="HELLOworld",
        msg="$concat should accept multiple expression arguments",
    ),
    ConcatTest(
        "expr_literal_and_expression",
        args=["hello", {"$toUpper": " world"}],
        expected="hello WORLD",
        msg="$concat should accept mix of literal and expression arguments",
    ),
    ConcatTest(
        "expr_mixed",
        args=[{"$toUpper": "a"}, "b", {"$toLower": "C"}],
        expected="Abc",
        msg="$concat should interleave expression and literal arguments",
    ),
]

# Property [Edge Cases]: long strings, special characters, JSON/BSON-meaningful characters, repeated
# args.
CONCAT_EDGE_TESTS: list[ConcatTest] = [
    # Special characters: newlines, tabs, null bytes
    ConcatTest(
        "edge_newline_tab",
        args=["line1\nline2", "\ttab"],
        expected="line1\nline2\ttab",
        msg="$concat should preserve newlines and tabs",
    ),
    ConcatTest(
        "edge_null_byte",
        args=["before\x00after", "ok"],
        expected="before\x00afterok",
        msg="$concat should preserve null bytes",
    ),
    # Characters meaningful in JSON/BSON
    ConcatTest(
        "edge_json_quote_backslash",
        args=['say "hi"', " and \\ backslash"],
        expected='say "hi" and \\ backslash',
        msg="$concat should preserve JSON quotes and backslashes",
    ),
    ConcatTest(
        "edge_json_braces_brackets",
        args=["{key}", "[val]"],
        expected="{key}[val]",
        msg="$concat should preserve braces and brackets",
    ),
    # All arguments are the same string
    ConcatTest(
        "edge_all_same",
        args=["abc", "abc", "abc"],
        expected="abcabcabc",
        msg="$concat should handle repeated identical arguments",
    ),
]

# Property [Nested Self-Application]: nested $concat within $concat produces the expected
# concatenated result.
CONCAT_NESTED_TESTS: list[ConcatTest] = [
    ConcatTest(
        "nested_one_level",
        args=[{"$concat": ["a", "b"]}, "c"],
        expected="abc",
        msg="$concat should accept nested $concat as argument",
    ),
]

CONCAT_INPUT_FORMS_TESTS = (
    CONCAT_ARITY_TESTS
    + CONCAT_ARITY_EMPTY
    + CONCAT_LARGE_ARITY_TESTS
    + CONCAT_EXPR_TESTS
    + CONCAT_EDGE_TESTS
    + CONCAT_NESTED_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_INPUT_FORMS_TESTS))
def test_concat_input_forms_cases(collection, test_case: ConcatTest):
    """Test $concat input form cases."""
    result = execute_expression(collection, {"$concat": test_case.args})
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
