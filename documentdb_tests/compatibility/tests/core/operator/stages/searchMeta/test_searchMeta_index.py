"""Tests for $searchMeta index selection and query modifier behavior."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

pytestmark = pytest.mark.requires(search=True)


# Property [Index Selection and Defaulting]: the index field names the search
# index to use, and omitting it or passing null selects the index named
# "default".
SEARCHMETA_INDEX_DEFAULTING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_explicit_default",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "index": "default",
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should select the default index when index is the literal "
        '"default", matching the omitted-index result',
    ),
    StageTestCase(
        "index_named_non_default",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "index": "alt_idx",
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should select a non-default index when its name matches",
    ),
    StageTestCase(
        "index_null_default",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "index": None,
                }
            }
        ],
        expected=[{"count": {"lowerBound": Int64(3)}}],
        msg="$searchMeta should treat a null index as field-absent and use the default index",
    ),
]

# Property [Index Nonexistent Silent Miss]: a well-formed but nonexistent index
# name returns a total-zero count without error; dollar-prefixed strings are
# taken as literal names, and a facet collector omits the facet field on a miss.
SEARCHMETA_INDEX_MISS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_nonexistent_silent_miss",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "index": "nope",
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should return a total-zero count without error for a "
        "nonexistent index name",
    ),
    StageTestCase(
        "index_dollar_field_literal",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "index": "$title",
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should treat a dollar-prefixed index as a literal nonexistent "
        "name rather than a field path",
    ),
    StageTestCase(
        "index_double_dollar_literal",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "index": "$$NOW",
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should treat a double-dollar index as a literal nonexistent "
        "name rather than a system variable",
    ),
    StageTestCase(
        "index_facet_nonexistent_omits_facet",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}}
                    },
                    "index": "nope",
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should omit the facet field and return a total-zero count when "
        "a facet collector targets a nonexistent index",
    ),
]

# Property [Index Name Matching and Character Handling]: index name matching is
# exact, case-sensitive, and not whitespace-trimmed; control characters, null
# bytes, Unicode, and long names are valid strings that miss silently with a
# total-zero count.
SEARCHMETA_INDEX_NAME_MATCHING_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"index_name_{suffix}",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "index": name,
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg=f"$searchMeta should treat a {suffix} index name as a nonexistent name and "
        "miss silently",
    )
    for name, suffix in [
        ("Default", "capitalized_default"),
        ("default ", "trailing_space_default"),
        (" default", "leading_space_default"),
        ("def ault", "embedded_space_default"),
        ("a\x00b", "embedded_null_byte"),
        ("\x00", "single_null_byte"),
        # Control characters U+0001, U+0002, U+001F.
        ("\x01\x02\x1f", "control_characters"),
        ("\t", "tab"),
        ("caf\u00e9_\u7d22\u5f15_\U0001f50d", "unicode"),
        ("x" * 10_000, "long_name"),
    ]
]

# Property [Modifier Coexistence]: the count and index modifiers coexist with a
# search operator in the same spec without being mistaken for operators.
SEARCHMETA_MODIFIER_COEXISTENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "coexist_operator_count_index",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "count": {"type": "total"},
                    "index": "default",
                }
            }
        ],
        expected=[{"count": {"total": Int64(3)}}],
        msg="$searchMeta should accept count and index modifiers alongside a search operator "
        "without mistaking them for operators",
    ),
]

# Property [Zero-Match Count]: a query matching no documents on an indexed
# collection returns a zero count respecting the requested count.type, defaulting
# to lowerBound.
SEARCHMETA_ZERO_MATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "zero_match_default",
        pipeline=[{"$searchMeta": {"text": {"query": "nonexistentxyz", "path": "title"}}}],
        expected=[{"count": {"lowerBound": INT64_ZERO}}],
        msg="$searchMeta should default to a lower-bound zero count for a zero-match query on "
        "an indexed collection",
    ),
    StageTestCase(
        "zero_match_total",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "nonexistentxyz", "path": "title"},
                    "count": {"type": "total"},
                }
            }
        ],
        expected=[{"count": {"total": INT64_ZERO}}],
        msg="$searchMeta should return a total-zero count for a zero-match query when count.type "
        "is total",
    ),
    StageTestCase(
        "zero_match_lower_bound",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "nonexistentxyz", "path": "title"},
                    "count": {"type": "lowerBound"},
                }
            }
        ],
        expected=[{"count": {"lowerBound": INT64_ZERO}}],
        msg="$searchMeta should return a lower-bound-zero count for a zero-match query when "
        "count.type is lowerBound",
    ),
]

SEARCHMETA_INDEX_TESTS: list[StageTestCase] = (
    SEARCHMETA_INDEX_DEFAULTING_TESTS
    + SEARCHMETA_INDEX_MISS_TESTS
    + SEARCHMETA_INDEX_NAME_MATCHING_TESTS
    + SEARCHMETA_MODIFIER_COEXISTENCE_TESTS
    + SEARCHMETA_ZERO_MATCH_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_INDEX_TESTS))
def test_searchMeta_index(search_collection, test_case: StageTestCase):
    """Test $searchMeta index selection and query modifier behavior."""
    result = execute_command(
        search_collection,
        {
            "aggregate": search_collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
