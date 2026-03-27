from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.test_case import BaseTestCase, pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.regexFindAll.utils.regexFindAll_common import (
    RegexFindAllTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)

# Property [Return Type - array]: result is always an array, even for no-match and null-propagation
# cases.
REGEXFINDALL_RETURN_TYPE_ARRAY_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "return_type_array_match",
        input="hello",
        regex="hello",
        msg="$regexFindAll should return array type when there is a match",
    ),
    RegexFindAllTest(
        "return_type_array_no_match",
        input="hello",
        regex="xyz",
        msg="$regexFindAll should return array type when there is no match",
    ),
    RegexFindAllTest(
        "return_type_array_null_input",
        input=None,
        regex="abc",
        msg="$regexFindAll should return array type when input is null",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_RETURN_TYPE_ARRAY_TESTS))
def test_regexfindall_return_type_array(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll result is always an array."""
    result = execute_expression(collection, {"$type": _expr(test_case)})
    assertSuccess(result, [{"result": "array"}], msg=test_case.msg)


# Property [Return Type - elements]: each element has match (string), idx (int), and captures (array
# of strings).
@dataclass(frozen=True)
class RegexFindAllReturnTypeElementTest(BaseTestCase):
    """Test case for $regexFindAll return type element verification."""

    input: Any = None
    regex: Any = None
    capture_element_types: list[str] | None = None


REGEXFINDALL_RETURN_TYPE_ELEMENT_TESTS: list[RegexFindAllReturnTypeElementTest] = [
    RegexFindAllReturnTypeElementTest(
        "return_type_elem_no_captures",
        input="hello",
        regex="hello",
        capture_element_types=[],
        msg="$regexFindAll match element should have string match, int idx, and empty captures",
    ),
    RegexFindAllReturnTypeElementTest(
        "return_type_elem_captures",
        input="abc 123",
        regex="([a-z]+) ([0-9]+)",
        capture_element_types=["string", "string"],
        msg="$regexFindAll match element captures should contain string-typed elements",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_RETURN_TYPE_ELEMENT_TESTS))
def test_regexfindall_return_type_elements(
    collection, test_case: RegexFindAllReturnTypeElementTest
):
    """Test $regexFindAll match element field types."""
    expr = {"$regexFindAll": {"input": test_case.input, "regex": test_case.regex}}
    first = {"$arrayElemAt": [expr, 0]}
    captures = {"$getField": {"field": "captures", "input": first}}
    result = execute_project(
        collection,
        {
            "matchType": {"$type": {"$getField": {"field": "match", "input": first}}},
            "idxType": {"$type": {"$getField": {"field": "idx", "input": first}}},
            "capturesType": {"$type": captures},
            "captureElementTypes": {"$map": {"input": captures, "as": "c", "in": {"$type": "$$c"}}},
        },
    )
    assertSuccess(
        result,
        [
            {
                "matchType": "string",
                "idxType": "int",
                "capturesType": "array",
                "captureElementTypes": test_case.capture_element_types,
            }
        ],
        msg=test_case.msg,
    )


# Property [Multiple Match Enumeration - idx ordering]: all idx values in the result are strictly
# increasing.
REGEXFINDALL_IDX_ORDERING_TESTS: list[RegexFindAllTest] = [
    RegexFindAllTest(
        "ordering_three_matches",
        input="abcabcabc",
        regex="abc",
        msg="$regexFindAll idx values should be strictly increasing for three adjacent matches",
    ),
    RegexFindAllTest(
        "ordering_scattered",
        input="aXbXc",
        regex="[abc]",
        msg="$regexFindAll idx should be strictly increasing for scattered single-char matches",
    ),
    RegexFindAllTest(
        "ordering_alternation",
        input="catXdogXfoxXdogXcat",
        regex="cat|dog|fox",
        msg="$regexFindAll idx values should be strictly increasing for alternation matches",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_IDX_ORDERING_TESTS))
def test_regexfindall_idx_ordering(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll idx values are strictly increasing."""
    result = execute_expression(collection, _expr(test_case))

    def _check(docs):
        matches = docs[0]["result"]
        idxs = [m["idx"] for m in matches]
        is_increasing = all(idxs[i] < idxs[i + 1] for i in range(len(idxs) - 1))
        return {"hasMultiple": len(idxs) >= 2, "isStrictlyIncreasing": is_increasing}

    assertSuccess(
        result,
        {"hasMultiple": True, "isStrictlyIncreasing": True},
        transform=_check,
        msg=test_case.msg,
    )


# Property [Multiple Match Enumeration - no overlap]: for non-zero-width matches, each subsequent
# match starts at or after the end of the previous match.
REGEXFINDALL_NO_OVERLAP_TESTS: list[RegexFindAllTest] = [
    # "aa" on "aaaa": non-overlapping gives 2 matches at 0 and 2, not 3 at 0, 1, 2.
    RegexFindAllTest(
        "no_overlap_could_overlap",
        input="aaaa",
        regex="aa",
        msg="$regexFindAll should not produce overlapping matches for 'aa' on 'aaaa'",
    ),
    # "aba" on "abababa": non-overlapping gives 2 matches at 0 and 4, not 3 at 0, 2, 4.
    RegexFindAllTest(
        "no_overlap_interleaved",
        input="abababa",
        regex="aba",
        msg="$regexFindAll should not produce overlapping matches for 'aba' on 'abababa'",
    ),
    RegexFindAllTest(
        "no_overlap_exact_adjacent",
        input="abcabcabc",
        regex="abc",
        msg="$regexFindAll should produce non-overlapping adjacent matches for 'abc' repeated",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REGEXFINDALL_NO_OVERLAP_TESTS))
def test_regexfindall_no_overlap(collection, test_case: RegexFindAllTest):
    """Test $regexFindAll non-zero-width matches do not overlap."""
    result = execute_expression(collection, _expr(test_case))

    def _check(docs):
        matches = docs[0]["result"]
        no_overlap = all(
            b["idx"] >= a["idx"] + len(a["match"]) for a, b in zip(matches, matches[1:])
        )
        return {"hasMultiple": len(matches) >= 2, "noOverlap": no_overlap}

    assertSuccess(
        result,
        {"hasMultiple": True, "noOverlap": True},
        transform=_check,
        msg=test_case.msg,
    )
