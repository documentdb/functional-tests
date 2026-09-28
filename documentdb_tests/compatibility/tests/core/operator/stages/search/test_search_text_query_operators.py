"""Tests for the $search queryString, term, and moreLikeThis operators."""

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


# Property [QueryString Lucene Syntax]: the queryString operator parses its query
# as Lucene syntax, so boolean operators and field-scoped terms take effect.
SEARCH_QUERY_STRING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "query_string_boolean_and",
        pipeline=[
            {"$search": {"queryString": {"query": "quick AND brown", "defaultPath": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search queryString should require every term of a boolean AND query to be present",
    ),
    StageTestCase(
        "query_string_score_boost",
        pipeline=[
            {
                "$search": {
                    "queryString": {
                        "query": "quick AND brown",
                        "defaultPath": "title",
                        "score": {"boost": {"value": 2.0}},
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search queryString should accept a score modifier and still return its matches",
    ),
    StageTestCase(
        "query_string_field_scoped",
        pipeline=[
            {"$search": {"queryString": {"query": "body:quick", "defaultPath": "title"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 2)]},
        msg="$search queryString should restrict a field-scoped term to the named field",
    ),
]

# Property [Term Token Match]: the deprecated term operator executes a token
# match against the index, returning the documents whose covered path contains
# the query token.
SEARCH_TERM_TESTS: list[StageTestCase] = [
    StageTestCase(
        "term_token_match_title",
        pipeline=[
            {"$search": {"term": {"path": "title", "query": "quick"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search term should execute a token match, returning the documents whose "
        "covered path contains the query token",
    ),
]

# Property [MoreLikeThis Similarity]: moreLikeThis analyzes the example text in
# like:{<field>:<text>} and returns the documents whose covered field shares its
# significant terms.
SEARCH_MORE_LIKE_THIS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "more_like_this_shared_terms",
        pipeline=[
            {"$search": {"moreLikeThis": {"like": {"title": "the quick brown fox"}}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search moreLikeThis should return the documents whose covered field shares the "
        "example text's significant terms",
    ),
    StageTestCase(
        "more_like_this_score_boost",
        pipeline=[
            {
                "$search": {
                    "moreLikeThis": {
                        "like": {"title": "the quick brown fox"},
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
        msg="$search moreLikeThis should accept a score modifier and still return its matches",
    ),
    StageTestCase(
        "more_like_this_array_of_docs",
        pipeline=[
            {
                "$search": {
                    "moreLikeThis": {
                        "like": [
                            {"title": "the quick brown fox"},
                            {"title": "quick rabbit"},
                        ]
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
        msg="$search moreLikeThis should accept an array of example documents and return the "
        "documents sharing their significant terms",
    ),
]

SEARCH_TEXT_QUERY_OPERATOR_TESTS = (
    SEARCH_QUERY_STRING_TESTS + SEARCH_TERM_TESTS + SEARCH_MORE_LIKE_THIS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_TEXT_QUERY_OPERATOR_TESTS))
def test_search_text_query_operators_cases(indexed_collection, test_case: StageTestCase):
    """Test $search queryString, term, and moreLikeThis operators."""
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


# Property [queryString Validation]: queryString requires query and defaultPath,
# both string-only (neither accepts the array form that term.query accepts).
SEARCH_QUERY_STRING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "query_string_missing_query",
        pipeline=[{"$search": {"queryString": {"defaultPath": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search queryString should reject an operator missing the required query",
    ),
    StageTestCase(
        "query_string_missing_default_path",
        pipeline=[{"$search": {"queryString": {"query": "quick"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search queryString should reject an operator missing the required defaultPath",
    ),
    *[
        StageTestCase(
            f"query_string_query_non_string_{tid}",
            pipeline=[{"$search": {"queryString": {"query": val, "defaultPath": "title"}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search queryString should reject a {tid} query as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"q": "quick"}),
            ("array", ["quick"]),
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
    *[
        StageTestCase(
            f"query_string_default_path_non_string_{tid}",
            pipeline=[{"$search": {"queryString": {"query": "quick", "defaultPath": val}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search queryString should reject a {tid} defaultPath as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"value": "title"}),
            ("array", ["title"]),
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

# Property [term Validation]: term requires path and query; term.path is a string,
# document, or array of paths, and term.query is a string or array of strings.
SEARCH_TERM_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "term_missing_path",
        pipeline=[{"$search": {"term": {"query": "quick"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search term should reject an operator missing the required path",
    ),
    StageTestCase(
        "term_missing_query",
        pipeline=[{"$search": {"term": {"path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search term should reject an operator missing the required query",
    ),
    *[
        StageTestCase(
            f"term_path_{tid}",
            pipeline=[{"$search": {"term": {"path": val, "query": "quick"}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search term should reject a {tid} path as neither a string, document, "
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
    *[
        StageTestCase(
            f"term_query_non_string_{tid}",
            pipeline=[{"$search": {"term": {"path": "title", "query": val}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search term should reject a {tid} query as a non-string",
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
]

# Property [moreLikeThis Validation]: moreLikeThis requires like, which must be a
# document or array of documents.
SEARCH_MORE_LIKE_THIS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "more_like_this_missing_like",
        pipeline=[{"$search": {"moreLikeThis": {}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search moreLikeThis should reject an operator missing the required like",
    ),
    *[
        StageTestCase(
            f"more_like_this_like_{tid}",
            pipeline=[{"$search": {"moreLikeThis": {"like": val}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search moreLikeThis should reject a {tid} like as neither a document nor array",
        )
        for tid, val in [
            ("string", "quick"),
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

SEARCH_TEXT_QUERY_OPERATOR_ERROR_TESTS = (
    SEARCH_QUERY_STRING_ERROR_TESTS + SEARCH_TERM_ERROR_TESTS + SEARCH_MORE_LIKE_THIS_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_TEXT_QUERY_OPERATOR_ERROR_TESTS))
def test_search_text_query_operators_errors(indexed_collection, test_case: StageTestCase):
    """Test $search queryString, term, and moreLikeThis required-field and type validation."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
