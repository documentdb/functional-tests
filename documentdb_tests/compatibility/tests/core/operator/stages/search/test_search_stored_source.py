"""Tests for the $search returnStoredSource option and behavior."""

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
    BSON_FIELD_NOT_BOOL_ERROR,
    SEARCH_EXECUTOR_ERROR,
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


_STORED_SOURCE_DOCS = [
    {"_id": 1, "title": "the quick brown fox", "body": "lazy dog"},
    {"_id": 2, "title": "slow green turtle", "body": "quick nap"},
    {"_id": 3, "title": "a quick quick rabbit", "body": "fast"},
]

_STORED_SOURCE_INDEX_DEFINITION = {
    "mappings": {"dynamic": True},
    "storedSource": {"include": ["title"]},
}


@pytest.fixture(scope="module")
def stored_source_collection(engine_client, worker_id):
    """A module-scoped collection with a storedSource-configured search index that
    stores only the title field, shared read-only across the returnStoredSource
    cases so the index is built and polled once."""
    db_name = fixtures.generate_database_name("stages_search_stored_source", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["stored_source"]
    coll.insert_many(_STORED_SOURCE_DOCS)
    create_search_index(coll, _STORED_SOURCE_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [ReturnStoredSource False Acceptance]: returnStoredSource accepts a
# boolean false with no coercion and the search still returns its matches (true
# is owned by the stored-source return property).
SEARCH_RETURN_STORED_SOURCE_FALSE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "return_stored_source_false",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "returnStoredSource": False}},
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 3),
                Contains("_id", 4),
            ]
        },
        msg="$search should accept returnStoredSource false and still return its matches",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_RETURN_STORED_SOURCE_FALSE_TESTS))
def test_search_return_stored_source_false_cases(indexed_collection, test_case: StageTestCase):
    """Test $search accepts returnStoredSource false."""
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


# Property [Stored Source Return]: returnStoredSource true against a
# storedSource-configured index returns the stored-source documents, exposing
# only the configured stored fields and omitting the unstored fields.
SEARCH_STORED_SOURCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "return_stored_source_projects_stored_fields",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "returnStoredSource": True}}
        ],
        expected=[
            {"_id": 1, "title": "the quick brown fox"},
            {"_id": 3, "title": "a quick quick rabbit"},
        ],
        msg="$search returnStoredSource true should return the stored-source documents "
        "exposing only the configured stored fields",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_STORED_SOURCE_TESTS))
def test_search_return_stored_source(stored_source_collection, test_case: StageTestCase):
    """Test $search returnStoredSource true returns the stored-source documents."""
    result = execute_command(
        stored_source_collection,
        {"aggregate": stored_source_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        ignore_doc_order=True,
    )


# Property [ReturnStoredSource Without Configured Source]: returnStoredSource true
# against an index that does not configure storedSource is rejected.
SEARCH_RETURN_STORED_SOURCE_CONFIG_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "return_stored_source_unconfigured",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "returnStoredSource": True}},
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search should reject returnStoredSource true against an index with no "
        "storedSource configured",
    ),
]

# Property [ReturnStoredSource Boolean Type]: the returnStoredSource option is
# strictly boolean with no coercion, and a null is not treated as a missing value.
SEARCH_RETURN_STORED_SOURCE_BOOL_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"return_stored_source_bool_type_{tid}",
        pipeline=[
            {"$search": {"text": {"query": "quick", "path": "title"}, "returnStoredSource": val}},
        ],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg=f"$search should reject a {tid} returnStoredSource as a non-boolean",
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

SEARCH_STORED_SOURCE_ERROR_TESTS = (
    SEARCH_RETURN_STORED_SOURCE_CONFIG_ERROR_TESTS
    + SEARCH_RETURN_STORED_SOURCE_BOOL_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_STORED_SOURCE_ERROR_TESTS))
def test_search_stored_source_errors(indexed_collection, test_case: StageTestCase):
    """Test $search returnStoredSource config and bool-type validation errors."""
    result = execute_command(
        indexed_collection,
        {"aggregate": indexed_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
