from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.replaceOne_common import (
    ReplaceOneTest,
    _expr,
)

# Property [Length Invariant]: when a match is found, result length equals
# len(input) - len(find) + len(replacement). When no match is found, result
# length equals len(input).
REPLACEONE_LENGTH_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "length_match_same_size",
        input="hello",
        find="h",
        replacement="j",
        msg="$replaceOne length invariant: match same size",
    ),
    ReplaceOneTest(
        "length_match_longer_replacement",
        input="hello",
        find="h",
        replacement="xyz",
        msg="$replaceOne length invariant: match longer replacement",
    ),
    ReplaceOneTest(
        "length_match_shorter_replacement",
        input="hello",
        find="hel",
        replacement="x",
        msg="$replaceOne length invariant: match shorter replacement",
    ),
    ReplaceOneTest(
        "length_match_empty_replacement",
        input="hello",
        find="hello",
        replacement="",
        msg="$replaceOne length invariant: match empty replacement",
    ),
    ReplaceOneTest(
        "length_empty_find_prepend",
        input="hello",
        find="",
        replacement="abc",
        msg="$replaceOne length invariant: empty find prepend",
    ),
    ReplaceOneTest(
        "length_no_match",
        input="hello",
        find="xyz",
        replacement="abc",
        msg="$replaceOne length invariant: no match",
    ),
    ReplaceOneTest(
        "length_multibyte",
        input="café",
        find="é",
        replacement="ee",
        msg="$replaceOne length invariant: multibyte",
    ),
    ReplaceOneTest(
        "length_4byte_to_1byte",
        input="a😀b",
        find="😀",
        replacement="X",
        msg="$replaceOne length invariant: 4byte to 1byte",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_LENGTH_TESTS))
def test_replaceone_length_invariant(collection, test_case: ReplaceOneTest):
    """Test $replaceOne result length invariant."""
    expr = _expr(test_case)
    input_len = {"$strLenCP": test_case.input}
    find_len = {"$strLenCP": test_case.find}
    replacement_len = {"$strLenCP": test_case.replacement}
    matched = {"$gte": [{"$indexOfCP": [test_case.input, test_case.find]}, 0]}
    expected_len = {
        "$add": [
            input_len,
            {
                "$cond": {
                    "if": matched,
                    "then": {"$subtract": [replacement_len, find_len]},
                    "else": 0,
                }
            },
        ]
    }
    result = execute_project(
        collection,
        {"lengthMatch": {"$eq": [{"$strLenCP": expr}, expected_len]}},
    )
    assertSuccess(result, [{"lengthMatch": True}], msg=test_case.msg)


# Property [Return Type]: the result is always a string when all arguments are
# non-null strings.
REPLACEONE_RETURN_TYPE_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "return_type_match",
        input="hello",
        find="h",
        replacement="j",
        msg="$replaceOne should return string for match",
    ),
    ReplaceOneTest(
        "return_type_no_match",
        input="hello",
        find="x",
        replacement="y",
        msg="$replaceOne should return string for no match",
    ),
    ReplaceOneTest(
        "return_type_all_empty",
        input="",
        find="",
        replacement="",
        msg="$replaceOne should return string for all empty",
    ),
    ReplaceOneTest(
        "return_type_unicode",
        input="café",
        find="é",
        replacement="e",
        msg="$replaceOne should return string for unicode",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_RETURN_TYPE_TESTS))
def test_replaceone_return_type(collection, test_case: ReplaceOneTest):
    """Test $replaceOne result is always type string."""
    result = execute_expression(collection, {"$type": _expr(test_case)})
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)


# Property [Non-Idempotency]: applying $replaceOne twice replaces successive occurrences,
# producing a different result than applying it once when multiple matches exist.
def test_replaceone_successive_application(collection):
    """Test $replaceOne replaces successive occurrences on repeated application."""
    once = {"$replaceOne": {"input": "cat bat cat", "find": "cat", "replacement": "dog"}}
    twice = {"$replaceOne": {"input": once, "find": "cat", "replacement": "dog"}}
    result = execute_project(collection, {"once": once, "twice": twice})
    assertSuccess(
        result,
        [{"once": "dog bat cat", "twice": "dog bat dog"}],
        msg="$replaceOne applied twice should replace successive occurrences",
    )
