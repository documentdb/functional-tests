"""Tests for $search text operator and fuzzy validation errors."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    QUERY_CLAUSE_CAP,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    STRING_SIZE_LIMIT_BYTES,
)

pytestmark = pytest.mark.requires(search=True)


# Property [text query Validation]: text.query is required and must be a
# non-empty string or array of non-null strings.
SEARCH_TEXT_QUERY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "text_query_missing",
        pipeline=[{"$search": {"text": {"path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a text operator missing the required query",
    ),
    StageTestCase(
        "text_query_empty_string",
        pipeline=[{"$search": {"text": {"query": "", "path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an empty-string text.query",
    ),
    StageTestCase(
        "text_query_empty_array",
        pipeline=[{"$search": {"text": {"query": [], "path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an empty-array text.query",
    ),
    *[
        StageTestCase(
            f"text_query_non_string_{tid}",
            pipeline=[
                {"$search": {"text": {"query": val, "path": "title"}}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search should reject a {tid} text.query as a non-string",
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
        "text_query_array_element_null",
        pipeline=[
            {"$search": {"text": {"query": ["quick", None], "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a null query-array element",
    ),
    StageTestCase(
        "text_query_array_element_non_string",
        pipeline=[
            {"$search": {"text": {"query": ["quick", 1], "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a non-string query-array element",
    ),
]

# Property [text path Validation]: text.path is required and must be a string,
# document, or non-empty array, and a path document must carry a value and a
# configured multi-analyzer.
SEARCH_TEXT_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "text_path_missing",
        pipeline=[{"$search": {"text": {"query": "quick"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a text operator missing the required path",
    ),
    StageTestCase(
        "text_path_empty_array",
        pipeline=[{"$search": {"text": {"query": "quick", "path": []}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an empty-array text.path",
    ),
    *[
        StageTestCase(
            f"text_path_non_string_non_document_{tid}",
            pipeline=[
                {"$search": {"text": {"query": "quick", "path": val}}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search should reject a {tid} text.path as neither a string nor a document",
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
        "text_path_object_no_value",
        pipeline=[{"$search": {"text": {"query": "quick", "path": {}}}}],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a text.path document with no value field",
    ),
    StageTestCase(
        "text_path_object_absent_multi",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": {"value": "title", "multi": "nope"}}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a text.path document referencing an absent "
        "multi-analyzer config",
    ),
]

# Property [text matchCriteria Validation]: text.matchCriteria must be the string
# "all" or "any".
SEARCH_TEXT_MATCH_CRITERIA_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "text_match_criteria_bad_enum",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title", "matchCriteria": "none"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a matchCriteria outside the set [all, any]",
    ),
    *[
        StageTestCase(
            f"text_match_criteria_type_{tid}",
            pipeline=[
                {"$search": {"text": {"query": "quick", "path": "title", "matchCriteria": val}}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search should reject a {tid} matchCriteria as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"a": 1}),
            ("array", ["all"]),
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

# Property [text synonyms Validation]: text.synonyms must name a configured
# synonym mapping.
SEARCH_TEXT_SYNONYMS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "text_synonyms_unknown_name",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title", "synonyms": "nope"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a text.synonyms referencing an unknown synonym mapping name",
    ),
]

# Property [text fuzzy Validation]: text.fuzzy must be a document and rejects an
# unknown sub-field (a null fuzzy is treated as the default).
SEARCH_TEXT_FUZZY_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"text_fuzzy_type_{tid}",
            pipeline=[
                {"$search": {"text": {"query": "quick", "path": "title", "fuzzy": val}}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search should reject a {tid} text.fuzzy as a non-document",
        )
        for tid, val in [
            ("string", "x"),
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("array", [{}]),
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
        "text_fuzzy_unknown_subfield",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title", "fuzzy": {"bogus": 1}}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an unknown text.fuzzy sub-field",
    ),
]

# Property [text score Validation]: text.score must be a document (a null score
# is treated as the default).
SEARCH_TEXT_SCORE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"text_score_type_{tid}",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title", "score": val}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search should reject a {tid} text.score as a non-document",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("bool", True),
        ("array", [{}]),
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

# Property [Query/Token Size]: a query that resolves to more than the clause cap is
# rejected, whether from a long query array or from a single string the analyzer
# splits into many sub-tokens, so the cap is clause-count based, not a byte-size limit.
SEARCH_QUERY_TOKEN_SIZE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "query_array_over_clause_cap",
        pipeline=[
            {
                "$search": {
                    "text": {
                        "query": ["quick"] + [f"nomatch{i}" for i in range(QUERY_CLAUSE_CAP)],
                        "path": "title",
                    }
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a query array one past the inclusive clause cap",
    ),
    # The run spans the BSON string size limit; it is still rejected with the
    # clause-count error rather than a byte-size error.
    StageTestCase(
        "query_single_byte_run_over_cap",
        pipeline=[
            {"$search": {"text": {"query": "a" * STRING_SIZE_LIMIT_BYTES, "path": "title"}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a multi-megabyte single-character run the analyzer "
        "splits into more sub-tokens than the clause cap",
    ),
    StageTestCase(
        "query_multi_byte_run_over_cap",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "\u00e9" * (STRING_SIZE_LIMIT_BYTES // 2), "path": "title"}
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a multi-byte run at the same byte size, showing the "
        "cap is clause-count based and not byte based",
    ),
]

# Property [Fuzzy maxEdits Enum]: text.fuzzy.maxEdits accepts only 1 or 2, so any
# other integer value is rejected.
SEARCH_FUZZY_MAX_EDITS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"fuzzy_max_edits_{tid}",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title", "fuzzy": {"maxEdits": val}}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search should reject a fuzzy.maxEdits of {tid} outside the set 1 or 2",
    )
    for tid, val in [
        ("zero", 0),
        ("three", 3),
    ]
]

# Property [Fuzzy prefixLength Lower Bound]: a negative text.fuzzy.prefixLength is
# rejected.
SEARCH_FUZZY_PREFIX_LENGTH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "fuzzy_prefix_length_negative",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title", "fuzzy": {"prefixLength": -1}}
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a negative fuzzy.prefixLength",
    ),
]

# Property [Fuzzy maxExpansions Bounds]: text.fuzzy.maxExpansions must fall within
# 1..1000, so a value outside those bounds is rejected.
SEARCH_FUZZY_MAX_EXPANSIONS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"fuzzy_max_expansions_{tid}",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title", "fuzzy": {"maxExpansions": val}}
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search should reject a fuzzy.maxExpansions of {tid} outside the bounds 1 to 1000",
    )
    for tid, val in [
        ("zero", 0),
        ("over_max", 1001),
    ]
]

SEARCH_TEXT_ERROR_TESTS = (
    SEARCH_TEXT_QUERY_ERROR_TESTS
    + SEARCH_TEXT_PATH_ERROR_TESTS
    + SEARCH_TEXT_MATCH_CRITERIA_ERROR_TESTS
    + SEARCH_TEXT_SYNONYMS_ERROR_TESTS
    + SEARCH_TEXT_FUZZY_ERROR_TESTS
    + SEARCH_TEXT_SCORE_ERROR_TESTS
    + SEARCH_QUERY_TOKEN_SIZE_ERROR_TESTS
    + SEARCH_FUZZY_MAX_EDITS_ERROR_TESTS
    + SEARCH_FUZZY_PREFIX_LENGTH_ERROR_TESTS
    + SEARCH_FUZZY_MAX_EXPANSIONS_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_TEXT_ERROR_TESTS))
def test_search_text_errors(indexed_collection, test_case: StageTestCase):
    """Test $search text operator and fuzzy validation errors."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
