"""Tests for $lookup array localField and foreignField matching."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Array localField Matching]: when localField resolves to an
# array, each element is individually matched against scalar foreignField
# values.
LOOKUP_ARRAY_LOCAL_FIELD_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "array_elements_matched_individually",
        docs=[{"_id": 1, "lf": ["a", "b"]}],
        foreign_docs=[
            {"_id": 10, "ff": "a"},
            {"_id": 11, "ff": "b"},
            {"_id": 12, "ff": "c"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": ["a", "b"],
                "joined": [
                    {"_id": 10, "ff": "a"},
                    {"_id": 11, "ff": "b"},
                ],
            },
        ],
        msg=(
            "$lookup should match each element of an array localField"
            " individually against scalar foreignField values"
        ),
    ),
    LookupTestCase(
        "empty_array_matches_null_and_missing_foreign",
        docs=[{"_id": 1, "lf": []}],
        foreign_docs=[
            {"_id": 10, "ff": None},
            {"_id": 11},
            {"_id": 12, "ff": "x"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": [],
                "joined": [
                    {"_id": 10, "ff": None},
                    {"_id": 11},
                ],
            },
        ],
        msg=(
            "$lookup should match an empty array localField against foreign"
            " documents where foreignField is null or missing"
        ),
    ),
    LookupTestCase(
        "nested_array_unwrapped_one_level_only",
        docs=[{"_id": 1, "lf": [["a"]]}],
        foreign_docs=[
            {"_id": 10, "ff": ["a"]},
            {"_id": 11, "ff": "a"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": [["a"]],
                "joined": [{"_id": 10, "ff": ["a"]}],
            },
        ],
        msg=(
            '$lookup should unwrap nested arrays one level only so [["a"]]'
            ' matches foreignField ["a"] but not scalar "a"'
        ),
    ),
    LookupTestCase(
        "double_nested_array_matching",
        docs=[{"_id": 1, "lf": [[["a"]]]}],
        foreign_docs=[
            {"_id": 10, "ff": [["a"]]},
            {"_id": 11, "ff": [[["a"]]]},
            {"_id": 12, "ff": ["a"]},
            {"_id": 13, "ff": "a"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": [[["a"]]],
                "joined": [
                    {"_id": 10, "ff": [["a"]]},
                    {"_id": 11, "ff": [[["a"]]]},
                ],
            },
        ],
        msg=(
            '$lookup should match [[["a"]]] against [["a"]] (element'
            ' match) and [[["a"]]] (whole array match) but not'
            ' ["a"] or "a"'
        ),
    ),
    LookupTestCase(
        "null_element_in_array_matches_null_and_missing_foreign",
        docs=[{"_id": 1, "lf": ["a", None]}],
        foreign_docs=[
            {"_id": 10, "ff": "a"},
            {"_id": 11, "ff": None},
            {"_id": 12},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": ["a", None],
                "joined": [
                    {"_id": 10, "ff": "a"},
                    {"_id": 11, "ff": None},
                    {"_id": 12},
                ],
            },
        ],
        msg=(
            "$lookup should match a null element in an array localField"
            " against foreign documents where foreignField is null or missing"
        ),
    ),
    LookupTestCase(
        "duplicate_elements_deduplicated",
        docs=[{"_id": 1, "lf": ["a", "a", "a"]}],
        foreign_docs=[{"_id": 10, "ff": "a"}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": ["a", "a", "a"],
                "joined": [{"_id": 10, "ff": "a"}],
            },
        ],
        msg=(
            "$lookup should deduplicate matching when localField array"
            " contains duplicate elements so each foreign document appears"
            " exactly once"
        ),
    ),
    LookupTestCase(
        "large_array_all_elements_matched",
        docs=[{"_id": 1, "lf": list(range(500))}],
        foreign_docs=[{"_id": i, "ff": i} for i in range(500)],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": list(range(500)),
                "joined": [{"_id": i, "ff": i} for i in range(500)],
            },
        ],
        msg=(
            "$lookup should correctly match all elements individually"
            " in a large array localField with 500 elements"
        ),
    ),
]

# Property [Array foreignField Matching]: when foreignField resolves to
# an array, each element is individually matched against scalar localField
# values.
LOOKUP_ARRAY_FOREIGN_FIELD_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "array_foreign_elements_matched_individually",
        docs=[{"_id": 1, "lf": "a"}, {"_id": 2, "lf": "c"}],
        foreign_docs=[
            {"_id": 10, "ff": ["a", "b"]},
            {"_id": 11, "ff": ["c", "d"]},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [{"_id": 10, "ff": ["a", "b"]}],
            },
            {
                "_id": 2,
                "lf": "c",
                "joined": [{"_id": 11, "ff": ["c", "d"]}],
            },
        ],
        msg=(
            "$lookup should match each element of an array foreignField"
            " individually against scalar localField values"
        ),
    ),
    LookupTestCase(
        "both_arrays_cross_matching",
        docs=[{"_id": 1, "lf": ["a", "b"]}],
        foreign_docs=[
            {"_id": 10, "ff": ["b", "c"]},
            {"_id": 11, "ff": ["d", "e"]},
            {"_id": 12, "ff": ["a", "x"]},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": ["a", "b"],
                "joined": [
                    {"_id": 10, "ff": ["b", "c"]},
                    {"_id": 12, "ff": ["a", "x"]},
                ],
            },
        ],
        msg=(
            "$lookup should cross-match when both localField and foreignField"
            " are arrays, matching any element in one against any element in"
            " the other"
        ),
    ),
]

# Property [Array foreignField Asymmetry]: array edge cases in
# foreignField do not resolve to missing the way symmetric localField
# cases do.
LOOKUP_ARRAY_FOREIGN_FIELD_ASYMMETRY_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "empty_array_foreign_does_not_match_null_or_missing_local",
        docs=[
            {"_id": 1},
            {"_id": 2, "lf": None},
            {"_id": 3, "lf": []},
        ],
        foreign_docs=[{"_id": 10, "ff": []}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "joined": []},
            {"_id": 2, "lf": None, "joined": []},
            {"_id": 3, "lf": [], "joined": []},
        ],
        msg=(
            "$lookup should not match empty array foreignField against"
            " null, missing, or empty array localField, unlike localField"
            " where [] matches null/missing foreign"
        ),
    ),
    LookupTestCase(
        "out_of_bounds_foreign_does_not_resolve_to_missing",
        docs=[
            {"_id": 1},
            {"_id": 2, "lf": None},
        ],
        foreign_docs=[{"_id": 10, "ff": ["a", "b"]}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff.99",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "joined": []},
            {"_id": 2, "lf": None, "joined": []},
        ],
        msg=(
            "$lookup should not match out-of-bounds foreignField index"
            " against null/missing localField, unlike localField where"
            " out-of-bounds resolves to missing and matches null/missing"
            " foreign"
        ),
    ),
    LookupTestCase(
        "negative_index_foreign_does_not_resolve_to_missing",
        docs=[
            {"_id": 1},
            {"_id": 2, "lf": None},
        ],
        foreign_docs=[{"_id": 10, "ff": ["a", "b"]}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff.-1",
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "joined": []},
            {"_id": 2, "lf": None, "joined": []},
        ],
        msg=(
            "$lookup should not match negative index foreignField against"
            " null/missing localField, unlike localField where negative"
            " index resolves to missing and matches null/missing foreign"
        ),
    ),
]

LOOKUP_ARRAY_FIELD_TESTS: list[LookupTestCase] = (
    LOOKUP_ARRAY_LOCAL_FIELD_TESTS
    + LOOKUP_ARRAY_FOREIGN_FIELD_TESTS
    + LOOKUP_ARRAY_FOREIGN_FIELD_ASYMMETRY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_ARRAY_FIELD_TESTS))
def test_lookup_array_fields(collection, test_case: LookupTestCase):
    """Test $lookup array field matching."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
