from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.ltrim_common import (
    _OMIT,
    LtrimTest,
    _expr,
)

# Property [Identity]: empty string chars is the identity element. The result equals input
# unchanged.
LTRIM_IDENTITY_TESTS: list[LtrimTest] = [
    LtrimTest(
        "identity_plain",
        input="hello",
        chars="",
        expected="hello",
        msg="$ltrim should return input unchanged when chars is empty",
    ),
    LtrimTest(
        "identity_leading_spaces",
        input="  hello",
        chars="",
        expected="  hello",
        msg="$ltrim should preserve leading spaces when chars is empty",
    ),
    LtrimTest(
        "identity_empty_input",
        input="",
        chars="",
        expected="",
        msg="$ltrim should return empty string when both input and chars are empty",
    ),
    LtrimTest(
        "identity_repeated_leading",
        input="aaahello",
        chars="",
        expected="aaahello",
        msg="$ltrim should preserve leading chars when chars is empty",
    ),
    LtrimTest(
        "identity_unicode",
        input="日本語",
        chars="",
        expected="日本語",
        msg="$ltrim should return Unicode input unchanged when chars is empty",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_IDENTITY_TESTS))
def test_ltrim_identity(collection, test_case: LtrimTest):
    """Test $ltrim identity cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Idempotency]: applying $ltrim twice with the same chars yields the same result as
# applying it once.
LTRIM_IDEMPOTENCY_TESTS: list[LtrimTest] = [
    LtrimTest(
        "idempotent_default",
        input="  hello",
        expected="hello",
        msg="$ltrim should be idempotent with default whitespace trimming",
    ),
    LtrimTest(
        "idempotent_custom",
        input="aaahello",
        chars="a",
        expected="hello",
        msg="$ltrim should be idempotent with custom chars",
    ),
    LtrimTest(
        "idempotent_mixed_whitespace",
        input=" \t\nhello",
        expected="hello",
        msg="$ltrim should be idempotent with mixed whitespace",
    ),
    LtrimTest(
        "idempotent_no_trim",
        input="hello",
        expected="hello",
        msg="$ltrim should be idempotent when no trimming occurs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_IDEMPOTENCY_TESTS))
def test_ltrim_idempotency(collection, test_case: LtrimTest):
    """Test $ltrim idempotency."""
    once = _expr(test_case)
    twice = {"$ltrim": {"input": once}}
    if test_case.chars is not _OMIT:
        twice["$ltrim"]["chars"] = test_case.chars
    result = execute_project(collection, {"once": once, "twice": twice})
    assertSuccess(
        result, [{"once": test_case.expected, "twice": test_case.expected}], msg=test_case.msg
    )


# Property [Suffix Invariant]: the result is always a suffix of the original input string.
LTRIM_SUFFIX_INVARIANT_TESTS: list[LtrimTest] = [
    LtrimTest(
        "suffix_default_trim",
        input="  hello",
        msg="$ltrim result should be a suffix of input after default trimming",
    ),
    LtrimTest(
        "suffix_custom_chars",
        input="aaahello",
        chars="a",
        msg="$ltrim result should be a suffix of input after custom char trimming",
    ),
    LtrimTest(
        "suffix_no_trim_needed",
        input="hello",
        msg="$ltrim result should be a suffix of input when no trimming needed",
    ),
    LtrimTest(
        "suffix_all_trimmed",
        input="   ",
        msg="$ltrim result should be a suffix of input when all chars trimmed",
    ),
    LtrimTest(
        "suffix_mixed_whitespace",
        input="\t\nhello world",
        msg="$ltrim result should be a suffix of input with mixed whitespace",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_SUFFIX_INVARIANT_TESTS))
def test_ltrim_suffix_invariant(collection, test_case: LtrimTest):
    """Test $ltrim result is always a suffix of the original input."""
    ltrim_result = _expr(test_case)
    input_len = {"$strLenCP": test_case.input}
    result_len = {"$strLenCP": ltrim_result}
    suffix = {
        "$substrCP": [
            test_case.input,
            {"$subtract": [input_len, result_len]},
            result_len,
        ]
    }
    result = execute_expression(collection, {"$eq": [ltrim_result, suffix]})
    assertSuccess(result, [{"result": True}], msg=test_case.msg)


# Property [First Char Invariant]: the first character of a non-empty result is not a member of
# the trim character set. Only tested with custom chars where membership can be checked
# server-side via $indexOfCP.
LTRIM_FIRST_CHAR_INVARIANT_TESTS: list[LtrimTest] = [
    LtrimTest(
        "first_char_single",
        input="aaahello",
        chars="a",
        msg="$ltrim result's first char should not be in single-char trim set",
    ),
    LtrimTest(
        "first_char_multi",
        input="abcdef",
        chars="abc",
        msg="$ltrim result's first char should not be in multi-char trim set",
    ),
    LtrimTest(
        "first_char_all_leading",
        input="xyzabc",
        chars="xyz",
        msg="$ltrim result's first char should not be in trim set after full leading trim",
    ),
    LtrimTest(
        "first_char_no_trim",
        input="hello",
        chars="xyz",
        msg="$ltrim result's first char should not be in trim set when no trimming occurs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_FIRST_CHAR_INVARIANT_TESTS))
def test_ltrim_first_char_invariant(collection, test_case: LtrimTest):
    """Test $ltrim result's first character is not in the trim set."""
    ltrim_result = _expr(test_case)
    result_len = {"$strLenCP": ltrim_result}
    first_char = {"$substrCP": [ltrim_result, 0, 1]}
    result = execute_project(
        collection,
        {
            "firstCharNotInChars": {
                "$cond": {
                    "if": {"$gt": [result_len, 0]},
                    "then": {"$eq": [{"$indexOfCP": [test_case.chars, first_char]}, -1]},
                    "else": True,
                }
            },
        },
    )
    assertSuccess(result, [{"firstCharNotInChars": True}], msg=test_case.msg)


# Property [Return Type]: the result is always a string when the expression succeeds and no null
# propagation occurs.
LTRIM_RETURN_TYPE_TESTS: list[LtrimTest] = [
    LtrimTest(
        "return_type_default_trim",
        input="  hello",
        msg="$ltrim should return string type after default trimming",
    ),
    LtrimTest(
        "return_type_custom_no_match",
        input="hello",
        chars="x",
        msg="$ltrim should return string type when custom chars don't match",
    ),
    LtrimTest(
        "return_type_custom_trim",
        input="aaahello",
        chars="a",
        msg="$ltrim should return string type after custom char trimming",
    ),
    LtrimTest(
        "return_type_empty", input="", msg="$ltrim should return string type for empty input"
    ),
    LtrimTest(
        "return_type_all_whitespace",
        input="   ",
        msg="$ltrim should return string type when all whitespace is trimmed",
    ),
    LtrimTest(
        "return_type_unicode",
        input="日本語",
        chars="日",
        msg="$ltrim should return string type after Unicode char trimming",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(LTRIM_RETURN_TYPE_TESTS))
def test_ltrim_return_type(collection, test_case: LtrimTest):
    """Test $ltrim result is always type string."""
    result = execute_expression(collection, {"$type": _expr(test_case)})
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)
