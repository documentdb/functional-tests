from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.trim_common import (
    _OMIT,
    TrimTest,
    _expr,
)

# Property [Identity]: empty string chars is the identity element. The result equals input
# unchanged.
TRIM_IDENTITY_TESTS: list[TrimTest] = [
    TrimTest(
        "identity_plain",
        input="hello",
        chars="",
        expected="hello",
        msg="$trim should return input unchanged when chars is empty",
    ),
    TrimTest(
        "identity_surrounding_spaces",
        input="  hello  ",
        chars="",
        expected="  hello  ",
        msg="$trim should preserve surrounding spaces when chars is empty",
    ),
    TrimTest(
        "identity_empty_input",
        input="",
        chars="",
        expected="",
        msg="$trim should return empty string when both input and chars are empty",
    ),
    TrimTest(
        "identity_repeated",
        input="aaahelloaaa",
        chars="",
        expected="aaahelloaaa",
        msg="$trim should preserve surrounding chars when chars is empty",
    ),
    TrimTest(
        "identity_unicode",
        input="日本語",
        chars="",
        expected="日本語",
        msg="$trim should return Unicode input unchanged when chars is empty",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_IDENTITY_TESTS))
def test_trim_identity(collection, test_case: TrimTest):
    """Test $trim identity cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Idempotency]: applying $trim twice with the same chars yields the same result as
# applying it once.
TRIM_IDEMPOTENCY_TESTS: list[TrimTest] = [
    TrimTest(
        "idempotent_default",
        input="  hello  ",
        expected="hello",
        msg="$trim should be idempotent with default whitespace trimming",
    ),
    TrimTest(
        "idempotent_custom",
        input="aaahelloaaa",
        chars="a",
        expected="hello",
        msg="$trim should be idempotent with custom chars",
    ),
    TrimTest(
        "idempotent_mixed_whitespace",
        input=" \t\nhello\n\t ",
        expected="hello",
        msg="$trim should be idempotent with mixed whitespace",
    ),
    TrimTest(
        "idempotent_no_trim",
        input="hello",
        expected="hello",
        msg="$trim should be idempotent when no trimming occurs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_IDEMPOTENCY_TESTS))
def test_trim_idempotency(collection, test_case: TrimTest):
    """Test $trim idempotency."""
    once = _expr(test_case)
    twice = {"$trim": {"input": once}}
    if test_case.chars is not _OMIT:
        twice["$trim"]["chars"] = test_case.chars
    result = execute_project(collection, {"once": once, "twice": twice})
    assertSuccess(
        result, [{"once": test_case.expected, "twice": test_case.expected}], msg=test_case.msg
    )


# Property [Substring Invariant]: the result is always a contiguous substring of the original
# input string.
TRIM_SUBSTRING_INVARIANT_TESTS: list[TrimTest] = [
    TrimTest(
        "substring_default_trim",
        input="  hello  ",
        msg="$trim result should be a contiguous substring of input after default trimming",
    ),
    TrimTest(
        "substring_custom_chars",
        input="aaahelloaaa",
        chars="a",
        msg="$trim result should be a contiguous substring of input after custom char trimming",
    ),
    TrimTest(
        "substring_no_trim_needed",
        input="hello",
        msg="$trim result should be a contiguous substring of input when no trimming needed",
    ),
    TrimTest(
        "substring_all_trimmed",
        input="   ",
        msg="$trim result should be a contiguous substring of input when all chars trimmed",
    ),
    TrimTest(
        "substring_mixed_whitespace",
        input="\t\nhello world\n\t",
        msg="$trim result should be a contiguous substring of input with mixed whitespace",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_SUBSTRING_INVARIANT_TESTS))
def test_trim_substring_invariant(collection, test_case: TrimTest):
    """Test $trim result is always a contiguous substring of the original input."""
    trim_result = _expr(test_case)
    result = execute_project(
        collection,
        {
            "isSubstring": {
                "$cond": {
                    "if": {"$eq": [{"$strLenCP": trim_result}, 0]},
                    "then": True,
                    "else": {"$gte": [{"$indexOfCP": [test_case.input, trim_result]}, 0]},
                }
            }
        },
    )
    assertSuccess(result, [{"isSubstring": True}], msg=test_case.msg)


# Property [First Char Invariant]: the first character of a non-empty result is not a member of
# the trim character set. Only tested with custom chars where membership can be checked
# server-side via $indexOfCP.
TRIM_FIRST_CHAR_INVARIANT_TESTS: list[TrimTest] = [
    TrimTest(
        "first_char_single",
        input="aaahelloaaa",
        chars="a",
        msg="$trim result's first char should not be in single-char trim set",
    ),
    TrimTest(
        "first_char_multi",
        input="abcdefabc",
        chars="abc",
        msg="$trim result's first char should not be in multi-char trim set",
    ),
    TrimTest(
        "first_char_all_leading",
        input="xyzabcxyz",
        chars="xyz",
        msg="$trim result's first char should not be in trim set after full trim",
    ),
    TrimTest(
        "first_char_no_trim",
        input="hello",
        chars="xyz",
        msg="$trim result's first char should not be in trim set when no trimming occurs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_FIRST_CHAR_INVARIANT_TESTS))
def test_trim_first_char_invariant(collection, test_case: TrimTest):
    """Test $trim result's first character is not in the trim set."""
    trim_result = _expr(test_case)
    result_len = {"$strLenCP": trim_result}
    first_char = {"$substrCP": [trim_result, 0, 1]}
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


# Property [Last Char Invariant]: the last character of a non-empty result is not a member of
# the trim character set. Only tested with custom chars where membership can be checked
# server-side via $indexOfCP.
TRIM_LAST_CHAR_INVARIANT_TESTS: list[TrimTest] = [
    TrimTest(
        "last_char_single",
        input="aaahelloaaa",
        chars="a",
        msg="$trim result's last char should not be in single-char trim set",
    ),
    TrimTest(
        "last_char_multi",
        input="abcdefabc",
        chars="abc",
        msg="$trim result's last char should not be in multi-char trim set",
    ),
    TrimTest(
        "last_char_all_trailing",
        input="xyzabcxyz",
        chars="xyz",
        msg="$trim result's last char should not be in trim set after full trim",
    ),
    TrimTest(
        "last_char_no_trim",
        input="hello",
        chars="xyz",
        msg="$trim result's last char should not be in trim set when no trimming occurs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_LAST_CHAR_INVARIANT_TESTS))
def test_trim_last_char_invariant(collection, test_case: TrimTest):
    """Test $trim result's last character is not in the trim set."""
    trim_result = _expr(test_case)
    result_len = {"$strLenCP": trim_result}
    last_char = {"$substrCP": [trim_result, {"$subtract": [result_len, 1]}, 1]}
    result = execute_project(
        collection,
        {
            "lastCharNotInChars": {
                "$cond": {
                    "if": {"$gt": [result_len, 0]},
                    "then": {"$eq": [{"$indexOfCP": [test_case.chars, last_char]}, -1]},
                    "else": True,
                }
            },
        },
    )
    assertSuccess(result, [{"lastCharNotInChars": True}], msg=test_case.msg)


# Property [Return Type]: the result is always a string when the expression succeeds and no null
# propagation occurs.
TRIM_RETURN_TYPE_TESTS: list[TrimTest] = [
    TrimTest(
        "return_type_default_trim",
        input="  hello  ",
        msg="$trim should return string type after default trimming",
    ),
    TrimTest(
        "return_type_custom_no_match",
        input="hello",
        chars="x",
        msg="$trim should return string type when custom chars don't match",
    ),
    TrimTest(
        "return_type_custom_trim",
        input="aaahelloaaa",
        chars="a",
        msg="$trim should return string type after custom char trimming",
    ),
    TrimTest("return_type_empty", input="", msg="$trim should return string type for empty input"),
    TrimTest(
        "return_type_all_whitespace",
        input="   ",
        msg="$trim should return string type when all whitespace is trimmed",
    ),
    TrimTest(
        "return_type_unicode",
        input="日本語",
        chars="日",
        msg="$trim should return string type after Unicode char trimming",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TRIM_RETURN_TYPE_TESTS))
def test_trim_return_type(collection, test_case: TrimTest):
    """Test $trim result is always type string."""
    result = execute_expression(collection, {"$type": _expr(test_case)})
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)
