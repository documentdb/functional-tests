from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.replaceAll_common import (
    ReplaceAllTest,
    _expr,
)

# Property [Length Invariant]: result length equals input length minus N * find length plus
# N * replacement length.
REPLACEALL_LENGTH_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "length_match_same_size",
        input="hello",
        find="h",
        replacement="j",
        msg="$replaceAll length invariant: match same size",
    ),
    ReplaceAllTest(
        "length_match_longer_replacement",
        input="hello",
        find="l",
        replacement="xyz",
        msg="$replaceAll length invariant: match longer replacement",
    ),
    ReplaceAllTest(
        "length_match_shorter_replacement",
        input="hello",
        find="hel",
        replacement="x",
        msg="$replaceAll length invariant: match shorter replacement",
    ),
    ReplaceAllTest(
        "length_match_empty_replacement",
        input="hello",
        find="hello",
        replacement="",
        msg="$replaceAll length invariant: match empty replacement",
    ),
    ReplaceAllTest(
        "length_empty_find",
        input="hello",
        find="",
        replacement="X",
        msg="$replaceAll length invariant: empty find",
    ),
    ReplaceAllTest(
        "length_no_match",
        input="hello",
        find="xyz",
        replacement="abc",
        msg="$replaceAll length invariant: no match",
    ),
    ReplaceAllTest(
        "length_multibyte",
        input="café",
        find="é",
        replacement="ee",
        msg="$replaceAll length invariant: multibyte",
    ),
    ReplaceAllTest(
        "length_4byte_to_1byte",
        input="a😀b😀c",
        find="😀",
        replacement="X",
        msg="$replaceAll length invariant: 4byte to 1byte",
    ),
    ReplaceAllTest(
        "length_multiple_matches",
        input="abcabcabc",
        find="abc",
        replacement="X",
        msg="$replaceAll length invariant: multiple matches",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_LENGTH_TESTS))
def test_replaceall_length_invariant(collection, test_case: ReplaceAllTest):
    """Test $replaceAll result length invariant."""
    expected_len = len(test_case.input.replace(test_case.find, test_case.replacement))
    result = execute_expression(collection, {"$strLenCP": _expr(test_case)})
    assertSuccess(result, [{"result": expected_len}], msg=test_case.msg)


# Property [Return Type]: the result is always a string when all arguments are non-null strings.
REPLACEALL_RETURN_TYPE_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "return_type_match",
        input="hello",
        find="h",
        replacement="j",
        msg="$replaceAll should return string for match",
    ),
    ReplaceAllTest(
        "return_type_no_match",
        input="hello",
        find="x",
        replacement="y",
        msg="$replaceAll should return string for no match",
    ),
    ReplaceAllTest(
        "return_type_all_empty",
        input="",
        find="",
        replacement="",
        msg="$replaceAll should return string for all empty",
    ),
    ReplaceAllTest(
        "return_type_unicode",
        input="café",
        find="é",
        replacement="e",
        msg="$replaceAll should return string for unicode",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_RETURN_TYPE_TESTS))
def test_replaceall_return_type(collection, test_case: ReplaceAllTest):
    """Test $replaceAll result is always type string."""
    result = execute_expression(collection, {"$type": _expr(test_case)})
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)


# Property [Idempotency]: applying $replaceAll twice with the same find/replacement yields the
# same result as applying it once, when the replacement does not contain the find string.
REPLACEALL_IDEMPOTENCY_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "idempotent_simple",
        input="cat bat cat",
        find="cat",
        replacement="dog",
        expected="dog bat dog",
        msg="$replaceAll should be idempotent when replacement does not contain find",
    ),
    ReplaceAllTest(
        "idempotent_no_match",
        input="hello",
        find="xyz",
        replacement="abc",
        expected="hello",
        msg="$replaceAll should be idempotent when find has no match",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_IDEMPOTENCY_TESTS))
def test_replaceall_idempotency(collection, test_case: ReplaceAllTest):
    """Test $replaceAll idempotency."""
    once = _expr(test_case)
    twice = {
        "$replaceAll": {"input": once, "find": test_case.find, "replacement": test_case.replacement}
    }
    result = execute_project(collection, {"once": once, "twice": twice})
    assertSuccess(
        result, [{"once": test_case.expected, "twice": test_case.expected}], msg=test_case.msg
    )
