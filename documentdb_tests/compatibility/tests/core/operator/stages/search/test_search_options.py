"""Tests for $search stage options (index, sort, tracking) and view resolution."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    SEARCH_INDEX_NAME,
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
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

pytestmark = pytest.mark.requires(search=True)


# Property [Index Option]: the index option names the search index to query, so
# a name no index has returns nothing silently, and any string is accepted with
# no validation error.
SEARCH_INDEX_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_named_existing",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "index": SEARCH_INDEX_NAME}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should query the index named by a non-empty string index option",
    ),
    StageTestCase(
        "index_nonexistent_silent",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "index": "no_such_index"}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should return no documents and no error for a nonexistent index name",
    ),
    StageTestCase(
        "index_name_1000_chars",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "index": "a" * 1_000}},
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should accept a 1000-character index name with no length validation",
    ),
    StageTestCase(
        "index_name_special_chars",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "index": "name with spaces!@#$%",
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should accept a special-character index name with no charset validation",
    ),
    StageTestCase(
        "index_name_unicode",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "index": "\u00edndax\u00f1\u00e9\U0001f600",
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$search should accept a Unicode index name with no charset validation",
    ),
]

# Property [Sort Option]: a sort option document is accepted as a tiebreaker and
# the search still returns its matches.
SEARCH_SORT_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_ascending",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "sort": {"_id": 1}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a single ascending sort key and still return its matches",
    ),
    StageTestCase(
        "sort_descending",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "sort": {"_id": -1}}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept a single descending sort key and still return its matches",
    ),
    StageTestCase(
        "sort_meta_search_score",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "sort": {"sc": {"$meta": "searchScore"}},
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
        msg="$search should accept a $meta searchScore sort key and still return its matches",
    ),
    StageTestCase(
        "sort_multi_key",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "sort": {"_id": 1, "title": 1},
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
        msg="$search should accept a multi-key sort tiebreaker and still return its matches",
    ),
    StageTestCase(
        "sort_meta_then_key",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "sort": {"sc": {"$meta": "searchScore"}, "_id": 1},
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
        msg="$search should accept a $meta key with a multi-key tiebreaker and still return "
        "its matches",
    ),
]

# Property [Tracking Option]: the tracking option is a recognized stage option
# and is accepted so the search still returns its matches.
SEARCH_TRACKING_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "tracking_recognized",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "tracking": {"searchTerms": "quick"},
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
        msg="$search should accept the tracking option and still return its matches",
    ),
]

# Property [Concurrent Option]: the concurrent option is a recognized boolean stage
# option, so both true and false are accepted with no coercion and the search
# still returns its matches.
SEARCH_CONCURRENT_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"concurrent_{label}",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "concurrent": val}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg=f"$search should accept a {label} concurrent option and still return its matches",
    )
    for label, val in [("true", True), ("false", False)]
]

SEARCH_OPTION_TESTS = (
    SEARCH_INDEX_OPTION_TESTS
    + SEARCH_SORT_OPTION_TESTS
    + SEARCH_TRACKING_OPTION_TESTS
    + SEARCH_CONCURRENT_OPTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_OPTION_TESTS))
def test_search_options_cases(indexed_collection, test_case: StageTestCase):
    """Test $search index, sort, and tracking stage options."""
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


# Property [View Index Resolution]: a $search against a view resolves the
# underlying collection's search index and returns the underlying collection's
# matching documents.
@pytest.mark.aggregate
def test_search_view_resolves_underlying_index(indexed_collection):
    """Test $search over a view resolves the underlying collection's search index."""
    db = indexed_collection.database
    view_name = "view_over_indexed"
    db.command({"create": view_name, "viewOn": indexed_collection.name, "pipeline": []})
    try:
        result = execute_command(
            db[view_name],
            {
                "aggregate": db[view_name].name,
                "pipeline": [{"$search": {"text": {"query": "quick", "path": "title"}}}],
                "cursor": {},
            },
        )
    finally:
        db.drop_collection(view_name)
    assertResult(
        result,
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search over a view should resolve the underlying collection's index for its matches",
        raw_res=True,
    )


# Property [Index Option Type And Value]: the index option must be a non-empty
# string (a null index is treated as the default).
SEARCH_INDEX_OPTION_ERROR_TESTS: list[StageTestCase] = [
    *[
        StageTestCase(
            f"index_type_{tid}",
            pipeline=[
                {"$search": {"text": {"query": "quick", "path": "title"}, "index": val}},
            ],
            error_code=UNKNOWN_ERROR,
            msg=f"$search should reject a {tid} index option as a non-string",
        )
        for tid, val in [
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.5),
            ("bool", True),
            ("object", {"name": "default"}),
            ("array", ["default"]),
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
        "index_empty_string",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "index": ""}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject an empty-string index option",
    ),
]

# Property [Sort Value Validation]: sort requires at least one field, rejects a
# direction other than 1 or -1, and rejects a $meta sort key other than
# searchScore.
SEARCH_SORT_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_empty",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "sort": {}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a sort document with no sort field",
    ),
    StageTestCase(
        "sort_bad_direction",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "sort": {"n": 2}}},
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a sort direction other than 1 or -1",
    ),
    StageTestCase(
        "sort_bad_meta_key",
        pipeline=[
            {
                "$search": {
                    "text": {"query": "quick", "path": "title"},
                    "sort": {"n": {"$meta": "bogus"}},
                }
            },
        ],
        error_code=UNKNOWN_ERROR,
        msg="$search should reject a $meta sort key other than searchScore",
    ),
]

# Property [Concurrent Option Type]: the concurrent option must be a boolean, so a
# value of any non-boolean BSON type is rejected with no coercion. A null concurrent
# is treated as the default (a success), so it is excluded.
SEARCH_CONCURRENT_OPTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"concurrent_type_{tid}",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "concurrent": val}},
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$search should reject a {tid} concurrent option as a non-boolean",
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

SEARCH_OPTION_ERROR_TESTS = (
    SEARCH_INDEX_OPTION_ERROR_TESTS
    + SEARCH_SORT_VALUE_ERROR_TESTS
    + SEARCH_CONCURRENT_OPTION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_OPTION_ERROR_TESTS))
def test_search_options_errors(indexed_collection, test_case: StageTestCase):
    """Test $search index and sort option validation errors."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
