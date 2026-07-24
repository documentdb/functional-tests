"""Tests for the $search phrase operator."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
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


# Property [phrase slop Proximity]: phrase.slop bounds how far apart the query
# terms may sit and still match: slop 0 requires strict adjacency and a positive
# integer permits that many intervening positions.
SEARCH_PHRASE_SLOP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "phrase_slop_0_adjacent",
        pipeline=[
            {"$search": {"phrase": {"query": "quick brown", "path": "title", "slop": 0}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search phrase with slop 0 should match adjacent query terms",
    ),
    StageTestCase(
        "phrase_score_boost",
        pipeline=[
            {
                "$search": {
                    "phrase": {
                        "query": "quick brown",
                        "path": "title",
                        "slop": 0,
                        "score": {"boost": {"value": 2.0}},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search phrase should accept a score modifier and still return its matches",
    ),
    StageTestCase(
        "phrase_slop_0_excludes_gap",
        pipeline=[
            {"$search": {"phrase": {"query": "quick fox", "path": "title", "slop": 0}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search phrase with slop 0 should require strict adjacency and exclude a "
        "document with an intervening token",
    ),
    StageTestCase(
        "phrase_slop_positive_int",
        pipeline=[
            {"$search": {"phrase": {"query": "quick fox", "path": "title", "slop": 1}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search phrase with a positive integer slop should permit the intervening token",
    ),
    StageTestCase(
        "phrase_slop_whole_double",
        pipeline=[
            {"$search": {"phrase": {"query": "quick fox", "path": "title", "slop": 2.0}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search phrase should accept a whole-number double slop as the proximity bound",
    ),
    StageTestCase(
        "phrase_slop_large",
        pipeline=[
            {"$search": {"phrase": {"query": "quick fox", "path": "title", "slop": 1_000_000}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search phrase should accept a very large slop as the proximity bound",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_PHRASE_SLOP_TESTS))
def test_search_phrase_slop_cases(indexed_collection, test_case: StageTestCase):
    """Test $search phrase slop proximity matching."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [phrase query Validation]: phrase.query is required and must be a
# string or array of non-null strings.
SEARCH_PHRASE_QUERY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "phrase_query_missing",
        pipeline=[{"$search": {"phrase": {"path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search phrase should reject an operator missing the required query",
    ),
    *[
        StageTestCase(
            f"phrase_query_non_string_{tid}",
            pipeline=[{"$search": {"phrase": {"query": val, "path": "title"}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search phrase should reject a {tid} query as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"q": "quick"}),
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
        "phrase_query_array_element_null",
        pipeline=[
            {"$search": {"phrase": {"query": ["quick brown", None], "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search phrase should reject a null query-array element",
    ),
    StageTestCase(
        "phrase_query_array_element_non_string",
        pipeline=[
            {"$search": {"phrase": {"query": ["quick brown", 1], "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search phrase should reject a non-string query-array element",
    ),
]

# Property [phrase path Validation]: phrase.path is required and must be a string,
# document, or array of paths.
SEARCH_PHRASE_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "phrase_path_missing",
        pipeline=[{"$search": {"phrase": {"query": "quick brown"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search phrase should reject an operator missing the required path",
    ),
    *[
        StageTestCase(
            f"phrase_path_{tid}",
            pipeline=[{"$search": {"phrase": {"query": "quick brown", "path": val}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search phrase should reject a {tid} path as neither a string, document, "
            "nor array",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
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

# Property [phrase fuzzy Rejection]: phrase does not accept a fuzzy sub-field.
SEARCH_PHRASE_FUZZY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "phrase_fuzzy_unrecognized",
        pipeline=[
            {"$search": {"phrase": {"query": "quick brown", "path": "title", "fuzzy": {}}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a phrase.fuzzy sub-field as unrecognized",
    ),
]

SEARCH_PHRASE_ERROR_TESTS = (
    SEARCH_PHRASE_QUERY_ERROR_TESTS
    + SEARCH_PHRASE_PATH_ERROR_TESTS
    + SEARCH_PHRASE_FUZZY_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_PHRASE_ERROR_TESTS))
def test_search_phrase_errors(indexed_collection, test_case: StageTestCase):
    """Test $search phrase rejects bad query/path values and an unsupported fuzzy sub-field."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
