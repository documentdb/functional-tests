"""Tests for the $search regex operator."""

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
    REGEX_PATTERN_LIMIT_BYTES,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Regex Analyzed Path Matching]: with allowAnalyzedField true, the regex
# operator matches against an analyzed path's tokens, returning the documents
# whose token satisfies the pattern.
SEARCH_REGEX_MATCHING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "regex_analyzed_prefix",
        pipeline=[
            {"$search": {"regex": {"query": "qu.*", "path": "title", "allowAnalyzedField": True}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search regex should match analyzed-path tokens against the pattern when "
        "allowAnalyzedField is true",
    ),
    StageTestCase(
        "regex_score_boost",
        pipeline=[
            {
                "$search": {
                    "regex": {
                        "query": "qu.*",
                        "path": "title",
                        "allowAnalyzedField": True,
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
        msg="$search regex should accept a score modifier and still return its matches",
    ),
    StageTestCase(
        "regex_analyzed_distinct_token",
        pipeline=[
            {"$search": {"regex": {"query": "tur.*", "path": "title", "allowAnalyzedField": True}}},
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 2)]},
        msg="$search regex should match only the documents whose analyzed token satisfies "
        "the pattern",
    ),
]

# Property [Regex Pattern Length]: the regex operator imposes no byte-based
# pattern-length limit.
SEARCH_REGEX_PATTERN_LENGTH_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"regex_pattern_length_{n}",
        pipeline=[
            {"$search": {"regex": {"query": "a" * n, "path": "title", "allowAnalyzedField": True}}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg=f"$search regex should accept a {n}-byte pattern with no byte-based length limit",
    )
    for n in [
        REGEX_PATTERN_LIMIT_BYTES - 1,
        REGEX_PATTERN_LIMIT_BYTES,
        REGEX_PATTERN_LIMIT_BYTES + 1,
        100_000,
    ]
]

# Property [Regex Query Array OR]: regex.query accepts an array of patterns, matching
# the union of the documents matched by each element pattern.
SEARCH_REGEX_QUERY_ARRAY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "regex_query_array_or",
        pipeline=[
            {
                "$search": {
                    "regex": {
                        "query": ["qu.*", "tur.*"],
                        "path": "title",
                        "allowAnalyzedField": True,
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(4),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search regex should match the union of a multi-element query array's patterns",
    ),
]

SEARCH_REGEX_TESTS = (
    SEARCH_REGEX_MATCHING_TESTS + SEARCH_REGEX_PATTERN_LENGTH_TESTS + SEARCH_REGEX_QUERY_ARRAY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_REGEX_TESTS))
def test_search_regex_cases(indexed_collection, test_case: StageTestCase):
    """Test $search regex matching and pattern length."""
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


# Property [Regex Analyzed Path Rejection]: regex rejects a path that resolves to
# an analyzed (non-keyword) field unless allowAnalyzedField is true.
SEARCH_REGEX_ANALYZED_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "regex_analyzed_path_no_flag",
        pipeline=[
            {"$search": {"regex": {"query": "qu.*", "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search regex should reject an analyzed path when allowAnalyzedField is omitted",
    ),
]

# Property [Regex query Validation]: regex.query is required and must be a string
# or a non-empty array of non-null strings.
SEARCH_REGEX_QUERY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "regex_query_missing",
        pipeline=[{"$search": {"regex": {"path": "title", "allowAnalyzedField": True}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search regex should reject an operator missing the required query",
    ),
    *[
        StageTestCase(
            f"regex_query_non_string_{tid}",
            pipeline=[
                {"$search": {"regex": {"query": val, "path": "title", "allowAnalyzedField": True}}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search regex should reject a {tid} query as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"q": "qu.*"}),
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
        "regex_query_empty_array",
        pipeline=[
            {"$search": {"regex": {"query": [], "path": "title", "allowAnalyzedField": True}}}
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search regex should reject an empty-array query",
    ),
    StageTestCase(
        "regex_query_array_element_null",
        pipeline=[
            {
                "$search": {
                    "regex": {"query": ["qu.*", None], "path": "title", "allowAnalyzedField": True}
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search regex should reject a null query-array element",
    ),
    StageTestCase(
        "regex_query_array_element_non_string",
        pipeline=[
            {
                "$search": {
                    "regex": {"query": ["qu.*", 1], "path": "title", "allowAnalyzedField": True}
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search regex should reject a non-string query-array element",
    ),
]

# Property [Regex allowAnalyzedField Type]: allowAnalyzedField must be a boolean.
SEARCH_REGEX_ALLOW_ANALYZED_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"regex_allow_analyzed_{tid}",
        pipeline=[
            {"$search": {"regex": {"query": "qu.*", "path": "title", "allowAnalyzedField": val}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search regex should reject a {tid} allowAnalyzedField as a non-boolean",
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

# Property [Regex path Validation]: regex.path is required and must be a string,
# document, or array of paths.
SEARCH_REGEX_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "regex_path_missing",
        pipeline=[{"$search": {"regex": {"query": "qu.*", "allowAnalyzedField": True}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search regex should reject an operator missing the required path",
    ),
    *[
        StageTestCase(
            f"regex_path_{tid}",
            pipeline=[
                {"$search": {"regex": {"query": "qu.*", "path": val, "allowAnalyzedField": True}}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search regex should reject a {tid} path as neither a string, document, "
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

SEARCH_REGEX_ERROR_TESTS = (
    SEARCH_REGEX_ANALYZED_PATH_ERROR_TESTS
    + SEARCH_REGEX_QUERY_ERROR_TESTS
    + SEARCH_REGEX_ALLOW_ANALYZED_TYPE_ERROR_TESTS
    + SEARCH_REGEX_PATH_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_REGEX_ERROR_TESTS))
def test_search_regex_errors(indexed_collection, test_case: StageTestCase):
    """Test $search regex rejects analyzed paths and bad query/allowAnalyzedField/path values."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
