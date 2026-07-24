"""Tests for $search score ordering and scoreDetails."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BSON_FIELD_NOT_BOOL_ERROR,
    QUERY_METADATA_NOT_AVAILABLE_ERROR,
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Eq,
    Exists,
    Gt,
    Len,
    NonEmptyStr,
    PerDoc,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


# Property [SearchScore Ordering]: results are returned in descending searchScore
# order so the document with the highest matching-term frequency ranks first, and
# {$meta: "searchScore"} projects a positive float for every result.
SEARCH_SCORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_term_frequency_ordering",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}}},
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=PerDoc(
            {"_id": Eq(3), "score": Gt(0)},
            {"_id": Eq(4), "score": Gt(0)},
            {"_id": Eq(1), "score": Gt(0)},
        ),
        msg="$search should order results by descending searchScore, ranking the "
        "highest term-frequency document first",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SCORE_TESTS))
def test_search_score_ordering(indexed_collection, test_case: StageTestCase):
    """Test $search orders results by descending searchScore."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)


# Property [ScoreDetails Output]: with scoreDetails enabled, {$meta: "scoreDetails"}
# projects a recursive object with a positive value, a populated description
# string, and a populated details array.
SEARCH_SCORE_DETAILS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_details_shape",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "scoreDetails": True}},
            {"$limit": 1},
            {"$project": {"_id": 0, "sd": {"$meta": "scoreDetails"}}},
        ],
        expected={
            "sd.value": Gt(0),
            "sd.description": NonEmptyStr(),
            "sd.details.0": Exists(),
        },
        msg="$search should project a recursive scoreDetails object with a value, "
        "description, and details array",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SCORE_DETAILS_TESTS))
def test_search_score_details(indexed_collection, test_case: StageTestCase):
    """Test $search projects the recursive scoreDetails shape (value, description, details)."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)


# Property [ScoreDetails Unavailable]: projecting {$meta: "scoreDetails"} without
# enabling scoreDetails on the $search stage is rejected because the metadata is
# not computed.
SEARCH_SCORE_DETAILS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_details_not_enabled",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}}},
            {"$project": {"_id": 1, "sd": {"$meta": "scoreDetails"}}},
        ],
        error_code=QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg="$search should reject a scoreDetails metadata projection when scoreDetails "
        "is not enabled",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SCORE_DETAILS_ERROR_TESTS))
def test_search_score_details_unavailable(indexed_collection, test_case: StageTestCase):
    """Test $search rejects a scoreDetails projection when scoreDetails is not enabled."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


# Property [ScoreDetails Boolean Type]: the scoreDetails option is strictly
# boolean with no coercion, and a null is not treated as a missing value.
SEARCH_SCORE_DETAILS_BOOL_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"score_details_bool_type_{tid}",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "scoreDetails": val}},
        ],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg=f"$search should reject a {tid} scoreDetails as a non-boolean",
    )
    for tid, val in [
        ("string", "true"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("object", {"a": 1}),
        ("array", [True]),
        ("objectid", ObjectId("0123456789abcdef01234567")),
        ("datetime", datetime.datetime(2020, 1, 1)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("null", None),
    ]
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SCORE_DETAILS_BOOL_TYPE_ERROR_TESTS))
def test_search_score_details_bool_error(indexed_collection, test_case: StageTestCase):
    """Test $search rejects a non-bool scoreDetails option value."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


# Property [Operator Score Modifier]: an operator score modifier accepts exactly
# one of boost, constant, or function. Each alters scoring without changing the
# matched set, so the search still returns its matches. This is a shared operator
# option (every operator accepts it), so it is covered once here rather than per
# operator.
SEARCH_SCORE_MODIFIER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_modifier_boost",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "quick",
                        "path": "title",
                        "score": {"boost": {"value": 2.0}},
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a boost score modifier and still return its matches",
    ),
    StageTestCase(
        "score_modifier_constant",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "quick",
                        "path": "title",
                        "score": {"constant": {"value": 5.0}},
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a constant score modifier and still return its matches",
    ),
    StageTestCase(
        "score_modifier_function",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "quick",
                        "path": "title",
                        "score": {"function": {"score": "relevance"}},
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a function score modifier and still return its matches",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SCORE_MODIFIER_TESTS))
def test_search_score_modifier(indexed_collection, test_case: StageTestCase):
    """Test $search accepts each operator score modifier variant."""
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


# Property [Operator Score Modifier Validity]: a score modifier must name exactly
# one of boost/constant/function, so an empty modifier and one naming more than
# one variant are each rejected.
SEARCH_SCORE_MODIFIER_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "score_modifier_empty",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title", "score": {}}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an empty score modifier naming no variant",
    ),
    StageTestCase(
        "score_modifier_multiple_variants",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": "quick",
                        "path": "title",
                        "score": {"boost": {"value": 2.0}, "constant": {"value": 5.0}},
                    }
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a score modifier naming more than one variant",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_SCORE_MODIFIER_ERROR_TESTS))
def test_search_score_modifier_errors(indexed_collection, test_case: StageTestCase):
    """Test $search rejects an empty or multi-variant score modifier."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
