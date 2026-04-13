from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.rtrim_common import (
    _OMIT,
    RtrimTest,
    _expr,
)

# Property [Identity]: empty string chars is the identity element. The result equals input
# unchanged.
RTRIM_IDENTITY_TESTS: list[RtrimTest] = [
    RtrimTest(
        "identity_plain",
        input="hello",
        chars="",
        expected="hello",
        msg="$rtrim should return input unchanged when chars is empty",
    ),
    RtrimTest(
        "identity_trailing_spaces",
        input="hello  ",
        chars="",
        expected="hello  ",
        msg="$rtrim should preserve trailing spaces when chars is empty",
    ),
    RtrimTest(
        "identity_empty_input",
        input="",
        chars="",
        expected="",
        msg="$rtrim should return empty string when both input and chars are empty",
    ),
    RtrimTest(
        "identity_repeated_trailing",
        input="helloaaa",
        chars="",
        expected="helloaaa",
        msg="$rtrim should preserve trailing chars when chars is empty",
    ),
    RtrimTest(
        "identity_unicode",
        input="日本語",
        chars="",
        expected="日本語",
        msg="$rtrim should return Unicode input unchanged when chars is empty",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_IDENTITY_TESTS))
def test_rtrim_identity(collection, test_case: RtrimTest):
    """Test $rtrim identity (empty chars)."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Idempotency]: applying $rtrim twice with the same chars yields the same result as
# applying it once.
RTRIM_IDEMPOTENCY_TESTS: list[RtrimTest] = [
    RtrimTest(
        "idempotent_default",
        input="hello  ",
        expected="hello",
        msg="$rtrim should be idempotent with default whitespace trimming",
    ),
    RtrimTest(
        "idempotent_custom",
        input="helloaaa",
        chars="a",
        expected="hello",
        msg="$rtrim should be idempotent with custom chars",
    ),
    RtrimTest(
        "idempotent_mixed_whitespace",
        input="hello \t\n",
        expected="hello",
        msg="$rtrim should be idempotent with mixed whitespace",
    ),
    RtrimTest(
        "idempotent_no_trim",
        input="hello",
        expected="hello",
        msg="$rtrim should be idempotent when no trimming occurs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_IDEMPOTENCY_TESTS))
def test_rtrim_idempotency(collection, test_case: RtrimTest):
    """Test $rtrim idempotency."""
    once = _expr(test_case)
    twice = {"$rtrim": {"input": once}}
    if test_case.chars is not _OMIT:
        twice["$rtrim"]["chars"] = test_case.chars
    result = execute_project(collection, {"once": once, "twice": twice})
    assertSuccess(
        result, [{"once": test_case.expected, "twice": test_case.expected}], msg=test_case.msg
    )


# Property [Prefix Invariant]: the result is always a prefix of the original input string.
RTRIM_PREFIX_INVARIANT_TESTS: list[RtrimTest] = [
    RtrimTest(
        "prefix_default_trim",
        input="hello  ",
        msg="$rtrim result should be a prefix of input after default trimming",
    ),
    RtrimTest(
        "prefix_custom_chars",
        input="helloaaa",
        chars="a",
        msg="$rtrim result should be a prefix of input after custom char trimming",
    ),
    RtrimTest(
        "prefix_no_trim_needed",
        input="hello",
        msg="$rtrim result should be a prefix of input when no trimming needed",
    ),
    RtrimTest(
        "prefix_all_trimmed",
        input="   ",
        msg="$rtrim result should be a prefix of input when all chars trimmed",
    ),
    RtrimTest(
        "prefix_mixed_whitespace",
        input="hello world\t\n",
        msg="$rtrim result should be a prefix of input with mixed whitespace",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_PREFIX_INVARIANT_TESTS))
def test_rtrim_prefix_invariant(collection, test_case: RtrimTest):
    """Test $rtrim result is always a prefix of the original input."""
    rtrim_result = _expr(test_case)
    result_len = {"$strLenCP": rtrim_result}
    prefix = {"$substrCP": [test_case.input, 0, result_len]}
    result = execute_expression(collection, {"$eq": [rtrim_result, prefix]})
    assertSuccess(result, [{"result": True}], msg=test_case.msg)


# Property [Last Char Invariant]: the last character of a non-empty result is not a member of
# the trim character set. Only tested with custom chars where membership can be checked
# server-side via $indexOfCP.
RTRIM_LAST_CHAR_INVARIANT_TESTS: list[RtrimTest] = [
    RtrimTest(
        "last_char_single",
        input="helloaaa",
        chars="a",
        msg="$rtrim result's last char should not be in single-char trim set",
    ),
    RtrimTest(
        "last_char_multi",
        input="defabc",
        chars="abc",
        msg="$rtrim result's last char should not be in multi-char trim set",
    ),
    RtrimTest(
        "last_char_all_trailing",
        input="abcxyz",
        chars="xyz",
        msg="$rtrim result's last char should not be in trim set after full trailing trim",
    ),
    RtrimTest(
        "last_char_no_trim",
        input="hello",
        chars="xyz",
        msg="$rtrim result's last char should not be in trim set when no trimming occurs",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_LAST_CHAR_INVARIANT_TESTS))
def test_rtrim_last_char_invariant(collection, test_case: RtrimTest):
    """Test $rtrim result's last character is not in the trim set."""
    rtrim_result = _expr(test_case)
    result_len = {"$strLenCP": rtrim_result}
    last_char = {"$substrCP": [rtrim_result, {"$subtract": [result_len, 1]}, 1]}
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
RTRIM_RETURN_TYPE_TESTS: list[RtrimTest] = [
    RtrimTest(
        "return_type_default_trim",
        input="hello  ",
        msg="$rtrim should return string type after default trimming",
    ),
    RtrimTest(
        "return_type_custom_no_match",
        input="hello",
        chars="x",
        msg="$rtrim should return string type when custom chars don't match",
    ),
    RtrimTest(
        "return_type_custom_trim",
        input="helloaaa",
        chars="a",
        msg="$rtrim should return string type after custom char trimming",
    ),
    RtrimTest(
        "return_type_empty", input="", msg="$rtrim should return string type for empty input"
    ),
    RtrimTest(
        "return_type_all_whitespace",
        input="   ",
        msg="$rtrim should return string type when all whitespace is trimmed",
    ),
    RtrimTest(
        "return_type_unicode",
        input="日本語",
        chars="語",
        msg="$rtrim should return string type after Unicode char trimming",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(RTRIM_RETURN_TYPE_TESTS))
def test_rtrim_return_type(collection, test_case: RtrimTest):
    """Test $rtrim result is always type string."""
    result = execute_expression(collection, {"$type": _expr(test_case)})
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)
