"""Tests for the $search wildcard operator."""

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


_WILDCARD_DOCS = [
    {"_id": 1, "kw": "quick", "std": "the quick brown fox", "tok": "quick"},
    {"_id": 2, "kw": "quack"},
    {"_id": 3, "kw": "axb"},
    {"_id": 4, "kw": "AXB"},
    {"_id": 5, "kw": "a*b"},  # literal asterisk
    {"_id": 6, "kw": "a?b"},  # literal question mark
    {"_id": 7, "kw": "ab"},  # zero characters between a and b
    {"_id": 8, "kw": "axxb"},  # two characters between a and b
]

_WILDCARD_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "kw": {"type": "string", "analyzer": "lucene.keyword"},
            "std": {"type": "string"},
            "tok": {"type": "token"},
        },
    }
}


@pytest.fixture(scope="module")
def wildcard_collection(engine_client, worker_id):
    """A module-scoped collection with a static search index mapping a
    keyword-analyzed, a standard-analyzed, and a token-typed field, shared
    read-only across the wildcard cases so the index is built and polled once."""
    db_name = fixtures.generate_database_name("stages_search_wildcard", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["wildcard"]
    coll.insert_many(_WILDCARD_DOCS)
    create_search_index(coll, _WILDCARD_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [Wildcard Field-Type Matching]: wildcard term-searches a
# keyword-analyzed path without a flag and a standard-analyzed path with
# allowAnalyzedField true, but never matches a token-typed field even with the
# flag (it passes the analyzed-field guard yet is not term-searchable).
SEARCH_WILDCARD_FIELD_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "wildcard_keyword_no_flag",
        pipeline=[
            {"$search": {"wildcard": {"query": "qu*", "path": "kw"}}},
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$search wildcard should match a keyword-analyzed path with no allowAnalyzedField flag",
    ),
    StageTestCase(
        "wildcard_standard_with_flag",
        pipeline=[
            {"$search": {"wildcard": {"query": "qu*", "path": "std", "allowAnalyzedField": True}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search wildcard should match a standard-analyzed path when allowAnalyzedField "
        "is true",
    ),
    StageTestCase(
        "wildcard_token_matches_nothing",
        pipeline=[
            {"$search": {"wildcard": {"query": "qu*", "path": "tok", "allowAnalyzedField": True}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search wildcard should match nothing on a token-typed field even with "
        "allowAnalyzedField true",
    ),
]

# Property [Wildcard Special Characters]: `*` matches zero-or-more characters,
# `?` matches exactly one character, and a backslash-escaped `\*`/`\?` matches a
# literal `*`/`?` character rather than acting as a wildcard.
SEARCH_WILDCARD_SPECIAL_CHAR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "wildcard_star_zero_or_more",
        pipeline=[
            {"$search": {"wildcard": {"query": "a*b", "path": "kw"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(5),
                Contains("_id", 3),
                Contains("_id", 5),
                Contains("_id", 6),
                Contains("_id", 7),
                Contains("_id", 8),
            ]
        },
        msg="$search wildcard `*` should match zero-or-more characters, including the "
        "zero-character and multi-character tokens",
    ),
    StageTestCase(
        "wildcard_question_exactly_one",
        pipeline=[
            {"$search": {"wildcard": {"query": "a?b", "path": "kw"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 3),
                Contains("_id", 5),
                Contains("_id", 6),
            ]
        },
        msg="$search wildcard `?` should match exactly one character, excluding the "
        "zero-character and two-character tokens",
    ),
    StageTestCase(
        "wildcard_escaped_star_literal",
        pipeline=[
            {"$search": {"wildcard": {"query": "a\\*b", "path": "kw"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 5)]},
        msg="$search wildcard should match a literal `*` for an escaped `\\*`, not as a wildcard",
    ),
    StageTestCase(
        "wildcard_escaped_question_literal",
        pipeline=[
            {"$search": {"wildcard": {"query": "a\\?b", "path": "kw"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 6)]},
        msg="$search wildcard should match a literal `?` for an escaped `\\?`, not as a wildcard",
    ),
]

# Property [Wildcard Keyword Case Sensitivity]: matching on a keyword path is
# case-sensitive.
SEARCH_WILDCARD_CASE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "wildcard_keyword_case_sensitive",
        pipeline=[
            {"$search": {"wildcard": {"query": "A*B", "path": "kw"}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 4)]},
        msg="$search wildcard on a keyword path should be case-sensitive, matching only the "
        "uppercase-stored token",
    ),
]

# Property [Wildcard Query Array OR]: a query array matches the union of the
# documents matched by each element pattern.
SEARCH_WILDCARD_QUERY_ARRAY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "wildcard_query_array_or",
        pipeline=[
            {"$search": {"wildcard": {"query": ["qu*", "axb"], "path": "kw"}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search wildcard should match the union of a multi-element query array's patterns",
    ),
]

# Property [Wildcard Path Forms]: the path accepts a {value} document, a
# {wildcard} document, and an array of paths in addition to a bare string, each
# resolving to the covered field(s) it names.
SEARCH_WILDCARD_PATH_FORMS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "wildcard_path_value_document",
        pipeline=[
            {"$search": {"wildcard": {"query": "quick", "path": {"value": "kw"}}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search wildcard should accept a {value} path document resolving to the named field",
    ),
    StageTestCase(
        "wildcard_path_wildcard_document",
        pipeline=[
            {
                "$search": {
                    "wildcard": {
                        "query": "quick",
                        "path": {"wildcard": "*"},
                        "allowAnalyzedField": True,
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search wildcard should accept a {wildcard} path document spanning every covered "
        "field",
    ),
    StageTestCase(
        "wildcard_path_array",
        pipeline=[
            {"$search": {"wildcard": {"query": "quick", "path": ["kw"]}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$search wildcard should accept an array of paths resolving to the named field",
    ),
]

SEARCH_WILDCARD_TESTS = (
    SEARCH_WILDCARD_FIELD_TYPE_TESTS
    + SEARCH_WILDCARD_SPECIAL_CHAR_TESTS
    + SEARCH_WILDCARD_CASE_TESTS
    + SEARCH_WILDCARD_QUERY_ARRAY_TESTS
    + SEARCH_WILDCARD_PATH_FORMS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_WILDCARD_TESTS))
def test_search_wildcard_cases(wildcard_collection, test_case: StageTestCase):
    """Test $search wildcard matching over keyword-, standard-, and token-mapped fields."""
    result = execute_command(
        wildcard_collection,
        {"aggregate": wildcard_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [Wildcard Analyzed Path Rejection]: wildcard rejects a path that
# resolves to a non-keyword analyzed field when allowAnalyzedField is not set,
# including an empty or dotted path that resolves to no keyword field.
SEARCH_WILDCARD_ANALYZED_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "wildcard_standard_path_no_flag",
        pipeline=[
            {"$search": {"wildcard": {"query": "qu*", "path": "std"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject a standard-analyzed path without allowAnalyzedField",
    ),
    StageTestCase(
        "wildcard_empty_path_no_flag",
        pipeline=[
            {"$search": {"wildcard": {"query": "qu*", "path": ""}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject an empty path that resolves to no keyword field",
    ),
    StageTestCase(
        "wildcard_dotted_path_no_flag",
        pipeline=[
            {"$search": {"wildcard": {"query": "qu*", "path": "a.b"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject a dotted path that resolves to no keyword field",
    ),
]

# Property [Wildcard allowAnalyzedField Type]: allowAnalyzedField must be a
# boolean (a null value is treated as the default).
SEARCH_WILDCARD_ALLOW_ANALYZED_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"wildcard_allow_analyzed_{tid}",
        pipeline=[
            {"$search": {"wildcard": {"query": "qu*", "path": "kw", "allowAnalyzedField": val}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search wildcard should reject a {tid} allowAnalyzedField as a non-boolean",
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
    ]
]

# Property [Wildcard query Validation]: wildcard.query is required and must be a
# non-empty string or array of non-null strings.
SEARCH_WILDCARD_QUERY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "wildcard_query_missing",
        pipeline=[{"$search": {"wildcard": {"path": "kw"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject an operator missing the required query",
    ),
    StageTestCase(
        "wildcard_query_null",
        pipeline=[
            {"$search": {"wildcard": {"query": None, "path": "kw"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject a null query treated as missing",
    ),
    StageTestCase(
        "wildcard_query_empty_string",
        pipeline=[{"$search": {"wildcard": {"query": "", "path": "kw"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject an empty-string query",
    ),
    StageTestCase(
        "wildcard_query_empty_array",
        pipeline=[{"$search": {"wildcard": {"query": [], "path": "kw"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject an empty-array query",
    ),
    *[
        StageTestCase(
            f"wildcard_query_non_string_{tid}",
            pipeline=[
                {"$search": {"wildcard": {"query": val, "path": "kw"}}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search wildcard should reject a {tid} query as a non-string",
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
        "wildcard_query_array_element_null",
        pipeline=[
            {"$search": {"wildcard": {"query": ["qu*", None], "path": "kw"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject a null query-array element",
    ),
    StageTestCase(
        "wildcard_query_array_element_non_string",
        pipeline=[
            {"$search": {"wildcard": {"query": ["qu*", 1], "path": "kw"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject a non-string query-array element",
    ),
]

# Property [Wildcard path Validation]: wildcard.path is required and must be a
# string, document, or array of paths.
SEARCH_WILDCARD_PATH_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"wildcard_path_{tid}",
            pipeline=[{"$search": {"wildcard": {"query": "qu*", "path": val}}}],
            error_code=UNKNOWN_ERROR,
            msg=f"$search wildcard should reject a {tid} path as neither a document, string, "
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
    StageTestCase(
        "wildcard_path_null",
        pipeline=[
            {"$search": {"wildcard": {"query": "qu*", "path": None}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search wildcard should reject a null path treated as missing",
    ),
]

SEARCH_WILDCARD_ERROR_TESTS = (
    SEARCH_WILDCARD_ANALYZED_PATH_ERROR_TESTS
    + SEARCH_WILDCARD_ALLOW_ANALYZED_TYPE_ERROR_TESTS
    + SEARCH_WILDCARD_QUERY_ERROR_TESTS
    + SEARCH_WILDCARD_PATH_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_WILDCARD_ERROR_TESTS))
def test_search_wildcard_errors(wildcard_collection, test_case: StageTestCase):
    """Test $search wildcard rejects analyzed paths and bad allowAnalyzedField/query/path values."""
    result = execute_command(
        wildcard_collection,
        {"aggregate": wildcard_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
