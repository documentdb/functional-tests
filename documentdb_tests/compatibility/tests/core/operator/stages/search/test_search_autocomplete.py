"""Tests for the $search autocomplete operator."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    create_search_index,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


_AUTOCOMPLETE_DOCS = [
    {"_id": 1, "ac": "september"},  # matches sep, sept, and the fuzzy typos
    {"_id": 2, "ac": "october"},  # control: shares no probed prefix
    {"_id": 3, "ac": "separate"},  # shares the sep prefix but not sept
    {"_id": 4, "ac": "quick brown"},  # two tokens for the tokenOrder cases
]

_AUTOCOMPLETE_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "ac": {"type": "autocomplete"},
        },
    }
}


@pytest.fixture(scope="module")
def autocomplete_collection(engine_client, worker_id):
    """A module-scoped collection with a static search index mapping an
    autocomplete-typed field, shared read-only across the autocomplete cases so
    the index is built and polled once."""
    db_name = fixtures.generate_database_name("stages_search_autocomplete", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["autocomplete"]
    coll.insert_many(_AUTOCOMPLETE_DOCS)
    create_search_index(coll, _AUTOCOMPLETE_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [Autocomplete Edge-Gram Prefix Matching]: on an autocomplete-mapped
# path the query matches stored tokens by edge-gram prefix.
SEARCH_AUTOCOMPLETE_PREFIX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_prefix_short",
        pipeline=[
            {"$search": {"autocomplete": {"path": "ac", "query": "sep"}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 3)]},
        msg="$search autocomplete should match every stored token sharing the query prefix",
    ),
    StageTestCase(
        "autocomplete_prefix_longer",
        pipeline=[
            {"$search": {"autocomplete": {"path": "ac", "query": "sept"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search autocomplete should match only the tokens extending the longer query prefix",
    ),
]

# Property [Autocomplete Fuzzy Matching]: autocomplete accepts a fuzzy.maxEdits of
# 1 or 2 and matches a query within that many edits of a stored token.
SEARCH_AUTOCOMPLETE_FUZZY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_fuzzy_max_edits_1",
        # "septemer" is one deletion (the "b") away from the stored "september".
        pipeline=[
            {
                "$search": {
                    "autocomplete": {
                        "path": "ac",
                        "query": "septemer",
                        "fuzzy": {"maxEdits": 1},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search autocomplete should match a query within one edit at fuzzy.maxEdits 1",
    ),
    StageTestCase(
        "autocomplete_fuzzy_max_edits_2",
        # "septmer" is two deletions (the "e" and the "b") from the stored "september".
        pipeline=[
            {
                "$search": {
                    "autocomplete": {"path": "ac", "query": "septmer", "fuzzy": {"maxEdits": 2}}
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search autocomplete should match a query within two edits at fuzzy.maxEdits 2",
    ),
]

# Property [Autocomplete Token Order]: tokenOrder "any" matches the query terms in
# any order while "sequential" requires them in the stored order.
SEARCH_AUTOCOMPLETE_TOKEN_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_token_order_any",
        pipeline=[
            {
                "$search": {
                    "autocomplete": {"path": "ac", "query": "brown quick", "tokenOrder": "any"}
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 4)]},
        msg="$search autocomplete tokenOrder any should match the query terms in any order",
    ),
    StageTestCase(
        "autocomplete_token_order_sequential_in_order",
        pipeline=[
            {
                "$search": {
                    "autocomplete": {
                        "path": "ac",
                        "query": "quick brown",
                        "tokenOrder": "sequential",
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 4)]},
        msg="$search autocomplete tokenOrder sequential should match terms in the stored order",
    ),
    StageTestCase(
        "autocomplete_token_order_sequential_reversed",
        pipeline=[
            {
                "$search": {
                    "autocomplete": {
                        "path": "ac",
                        "query": "brown quick",
                        "tokenOrder": "sequential",
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search autocomplete tokenOrder sequential should not match terms out of order",
    ),
]

# Property [Autocomplete Query Array OR]: autocomplete.query accepts an array of
# strings, matching the union of the documents matched by each element prefix.
SEARCH_AUTOCOMPLETE_QUERY_ARRAY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_query_array_or",
        pipeline=[
            {"$search": {"autocomplete": {"path": "ac", "query": ["sept", "octo"]}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$search autocomplete should match the union of a multi-element query array's prefixes",
    ),
]

# Property [Autocomplete Fuzzy prefixLength And maxExpansions]: autocomplete.fuzzy
# accepts prefixLength and maxExpansions, where prefixLength locks a
# code-point-counted prefix from edits (a typo inside the locked prefix does not
# match while prefixLength 0 still allows the fuzzy match) and maxExpansions is
# accepted across its 1..1000 bound.
SEARCH_AUTOCOMPLETE_FUZZY_PREFIX_EXPANSION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_fuzzy_prefix_unlocked",
        # "xeptember" is one substitution (x for s) at code point 0 from the stored
        # "september"; prefixLength 0 locks nothing so the edit is allowed.
        pipeline=[
            {
                "$search": {
                    "autocomplete": {
                        "path": "ac",
                        "query": "xeptember",
                        "fuzzy": {"maxEdits": 1, "prefixLength": 0},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search autocomplete should allow a fuzzy edit outside the prefix when "
        "prefixLength is 0",
    ),
    StageTestCase(
        "autocomplete_fuzzy_prefix_locked",
        # prefixLength 2 locks code points 0 and 1, so the substitution at code
        # point 0 falls inside the locked prefix and cannot match.
        pipeline=[
            {
                "$search": {
                    "autocomplete": {
                        "path": "ac",
                        "query": "xeptember",
                        "fuzzy": {"maxEdits": 1, "prefixLength": 2},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search autocomplete should lock the prefix from edits so a locked-prefix typo "
        "does not match",
    ),
    *[
        StageTestCase(
            f"autocomplete_fuzzy_max_expansions_{label}",
            # "septemer" is one deletion from the stored "september", matching only it
            # regardless of the maxExpansions bound.
            pipeline=[
                {
                    "$search": {
                        "autocomplete": {
                            "path": "ac",
                            "query": "septemer",
                            "fuzzy": {"maxEdits": 1, "maxExpansions": val},
                        }
                    }
                },
            ],
            expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
            msg=f"$search autocomplete should accept fuzzy.maxExpansions at the {label} bound "
            "and still match",
        )
        for label, val in [("lower", 1), ("upper", 1000)]
    ],
]

SEARCH_AUTOCOMPLETE_TESTS = (
    SEARCH_AUTOCOMPLETE_PREFIX_TESTS
    + SEARCH_AUTOCOMPLETE_FUZZY_TESTS
    + SEARCH_AUTOCOMPLETE_TOKEN_ORDER_TESTS
    + SEARCH_AUTOCOMPLETE_QUERY_ARRAY_TESTS
    + SEARCH_AUTOCOMPLETE_FUZZY_PREFIX_EXPANSION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_AUTOCOMPLETE_TESTS))
def test_search_autocomplete_cases(autocomplete_collection, test_case: StageTestCase):
    """Test $search autocomplete edge-gram prefix, fuzzy, and tokenOrder matching."""
    result = execute_command(
        autocomplete_collection,
        {"aggregate": autocomplete_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [Autocomplete Path Mapping Required]: autocomplete requires the queried
# path to be mapped as an autocomplete field.
SEARCH_AUTOCOMPLETE_PATH_MAPPING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_path_not_autocomplete_mapped",
        pipeline=[
            {"$search": {"autocomplete": {"path": "title", "query": "sep"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject a path with no autocomplete index field definition",
    ),
]

# Property [Autocomplete fuzzy.maxEdits Range]: autocomplete.fuzzy.maxEdits must
# be 1 or 2, so any value outside that range is rejected.
SEARCH_AUTOCOMPLETE_FUZZY_MAX_EDITS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"autocomplete_fuzzy_max_edits_{val}",
        pipeline=[
            {
                "$search": {
                    "autocomplete": {"path": "ac", "query": "sep", "fuzzy": {"maxEdits": val}}
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search autocomplete should reject a fuzzy.maxEdits of {val}, which is not 1 or 2",
    )
    for val in [0, 3]
]

# Property [Autocomplete tokenOrder Enum]: autocomplete.tokenOrder must be one of
# "any" or "sequential", so any other value is rejected.
SEARCH_AUTOCOMPLETE_TOKEN_ORDER_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_token_order_bogus",
        pipeline=[
            {"$search": {"autocomplete": {"path": "ac", "query": "sep", "tokenOrder": "bogus"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject a tokenOrder outside the [any, sequential] enum",
    ),
]

# Property [Autocomplete query Validation]: autocomplete.query is required and
# must be a non-empty string or array of non-null strings.
SEARCH_AUTOCOMPLETE_QUERY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_query_missing",
        pipeline=[{"$search": {"autocomplete": {"path": "ac"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject an operator missing the required query",
    ),
    StageTestCase(
        "autocomplete_query_empty_string",
        pipeline=[{"$search": {"autocomplete": {"path": "ac", "query": ""}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject an empty-string query",
    ),
    StageTestCase(
        "autocomplete_query_empty_array",
        pipeline=[{"$search": {"autocomplete": {"path": "ac", "query": []}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject an empty-array query",
    ),
    *[
        StageTestCase(
            f"autocomplete_query_non_string_{tid}",
            pipeline=[{"$search": {"autocomplete": {"path": "ac", "query": val}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search autocomplete should reject a {tid} query as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"q": "sep"}),
            ("objectid", ObjectId("0123456789abcdef01234567")),
            ("datetime", datetime.datetime(2020, 1, 1)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
        ]
    ],
    StageTestCase(
        "autocomplete_query_array_element_null",
        pipeline=[{"$search": {"autocomplete": {"path": "ac", "query": ["sep", None]}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject a null query-array element",
    ),
    StageTestCase(
        "autocomplete_query_array_element_non_string",
        pipeline=[{"$search": {"autocomplete": {"path": "ac", "query": ["sep", 1]}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject a non-string query-array element",
    ),
]

# Property [Autocomplete path Validation]: autocomplete.path is required and
# string-only, unlike the document and array forms text accepts.
SEARCH_AUTOCOMPLETE_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_path_missing",
        pipeline=[{"$search": {"autocomplete": {"query": "sep"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject an operator missing the required path",
    ),
    *[
        StageTestCase(
            f"autocomplete_path_{tid}",
            pipeline=[{"$search": {"autocomplete": {"path": val, "query": "sep"}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search autocomplete should reject a {tid} path as a non-string type",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"value": "ac"}),
            ("array", ["ac"]),
            ("objectid", ObjectId("0123456789abcdef01234567")),
            ("datetime", datetime.datetime(2020, 1, 1)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
        ]
    ],
]

# Property [Autocomplete fuzzy.prefixLength And maxExpansions Bounds]:
# autocomplete.fuzzy.prefixLength must be non-negative and maxExpansions must fall
# within 1..1000, so a negative prefixLength and a maxExpansions outside those
# bounds are rejected.
SEARCH_AUTOCOMPLETE_FUZZY_BOUNDS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "autocomplete_fuzzy_prefix_length_negative",
        pipeline=[
            {
                "$search": {
                    "autocomplete": {
                        "path": "ac",
                        "query": "sep",
                        "fuzzy": {"maxEdits": 1, "prefixLength": -1},
                    }
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search autocomplete should reject a negative fuzzy.prefixLength",
    ),
    *[
        StageTestCase(
            f"autocomplete_fuzzy_max_expansions_{label}",
            pipeline=[
                {
                    "$search": {
                        "autocomplete": {
                            "path": "ac",
                            "query": "sep",
                            "fuzzy": {"maxEdits": 1, "maxExpansions": val},
                        }
                    }
                },
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search autocomplete should reject a fuzzy.maxExpansions of {val} outside the "
            "bounds 1 to 1000",
        )
        for label, val in [("zero", 0), ("over_max", 1001)]
    ],
]

SEARCH_AUTOCOMPLETE_ERROR_TESTS = (
    SEARCH_AUTOCOMPLETE_PATH_MAPPING_ERROR_TESTS
    + SEARCH_AUTOCOMPLETE_FUZZY_MAX_EDITS_ERROR_TESTS
    + SEARCH_AUTOCOMPLETE_TOKEN_ORDER_ERROR_TESTS
    + SEARCH_AUTOCOMPLETE_QUERY_ERROR_TESTS
    + SEARCH_AUTOCOMPLETE_PATH_ERROR_TESTS
    + SEARCH_AUTOCOMPLETE_FUZZY_BOUNDS_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_AUTOCOMPLETE_ERROR_TESTS))
def test_search_autocomplete_errors(autocomplete_collection, test_case: StageTestCase):
    """Test $search autocomplete rejects unmapped paths and bad fuzzy.maxEdits/tokenOrder values."""
    result = execute_command(
        autocomplete_collection,
        {"aggregate": autocomplete_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
