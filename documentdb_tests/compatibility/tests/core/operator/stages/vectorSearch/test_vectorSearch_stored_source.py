"""Tests for the $vectorSearch stage: returnStoredSource behavior and errors."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest
from bson import (
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from bson.binary import Binary

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    NotExists,
    PerDoc,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

_INDEX_READY_TIMEOUT_SECONDS = 120

_STORED_SOURCE_CORPUS = [
    {
        "_id": 1,
        "name": "a",
        "title": "T1",
        "body": "B1",
        "embedding": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
    },
    {
        "_id": 2,
        "name": "b",
        "title": "T2",
        "body": "B2",
        "embedding": [DOUBLE_ZERO, 1.0, DOUBLE_ZERO],
    },
    # Doc 3 intentionally lacks the "title" field.
    {"_id": 3, "name": "c", "body": "B3", "embedding": [0.9, 0.1, DOUBLE_ZERO]},
]


@pytest.fixture(scope="module")
def stored_source_vector_search_collection(engine_client, worker_id):
    """Provide a collection with a READY vectorSearch index configured with storedSource."""
    db_name = f"vs_stored_source_{worker_id}"
    db = engine_client[db_name]
    coll = db["stored_source_vectors"]
    db.drop_collection(coll.name)
    db.create_collection(coll.name)
    coll.insert_many([dict(doc) for doc in _STORED_SOURCE_CORPUS])
    db.command(
        {
            "createSearchIndexes": coll.name,
            "indexes": [
                {
                    "name": "vs_stored_source_index",
                    "type": "vectorSearch",
                    "definition": {
                        "storedSource": {"include": ["name"]},
                        "fields": [
                            {
                                "type": "vector",
                                "path": "embedding",
                                "numDimensions": 3,
                                "similarity": "cosine",
                            },
                        ],
                    },
                }
            ],
        }
    )
    deadline = time.monotonic() + _INDEX_READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        indexes = list(coll.aggregate([{"$listSearchIndexes": {}}]))
        if indexes and indexes[0].get("status") == "READY":
            break
        time.sleep(2)
    else:
        raise TimeoutError("storedSource vectorSearch index did not reach READY state")
    yield coll
    engine_client.drop_database(db_name)


# Property [returnStoredSource Full Documents]: against a storedSource-configured
# index, both returnStoredSource false (the default) and true return the full
# document with all fields, because the configured stored-source field
# restriction is non-functional on this target.
VECTORSEARCH_RETURN_STORED_SOURCE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"return_stored_source_{tid}",
        collection_fixture="stored_source_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_stored_source_index",
                    "path": "embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "returnStoredSource": rss,
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=PerDoc(
            {"_id": Eq(1), "name": Eq("a"), "title": Eq("T1"), "body": Eq("B1")},
            {"_id": Eq(2), "name": Eq("b"), "title": Eq("T2"), "body": Eq("B2")},
            {"_id": Eq(3), "name": Eq("c"), "title": NotExists(), "body": Eq("B3")},
        ),
        msg=f"$vectorSearch should return the full document when returnStoredSource is {tid}",
    )
    for tid, rss in [("false", False), ("true", True)]
]

# Property [returnStoredSource Null As Omitted]: returnStoredSource null is
# treated as field-absent and the query succeeds with full documents as if the
# field were omitted, rather than triggering the not-configured error that
# returnStoredSource true raises on an index without a storedSource configuration.
VECTORSEARCH_RETURN_STORED_SOURCE_NULL_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "return_stored_source_null_omitted",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "returnStoredSource": None,
                }
            },
        ],
        expected=PerDoc(
            {"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}, {"_id": Eq(4)}, {"_id": Eq(5)}
        ),
        msg="$vectorSearch should treat returnStoredSource null as omitted and succeed "
        "on an index without a storedSource configuration",
    ),
]

# Property [returnStoredSource Type Rejection]: a non-boolean returnStoredSource
# value is rejected as not a boolean, with no coercion.
VECTORSEARCH_RETURN_STORED_SOURCE_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"return_stored_source_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "returnStoredSource": val,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} returnStoredSource value as a non-boolean",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("string", "true"),
        ("array", [True]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("5a9427648b0beebeb69537a5")),
        ("datetime", datetime(2020, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [returnStoredSource Not Configured]: returnStoredSource true against an
# index that has no storedSource configuration is rejected because stored source
# is not configured for that index.
VECTORSEARCH_RETURN_STORED_SOURCE_NOT_CONFIGURED_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "return_stored_source_not_configured",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "returnStoredSource": True,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject returnStoredSource true when the index has no "
        "storedSource configuration",
    ),
]

VECTORSEARCH_STORED_SOURCE_ALL_TESTS = (
    VECTORSEARCH_RETURN_STORED_SOURCE_TESTS
    + VECTORSEARCH_RETURN_STORED_SOURCE_NULL_TESTS
    + VECTORSEARCH_RETURN_STORED_SOURCE_TYPE_ERROR_TESTS
    + VECTORSEARCH_RETURN_STORED_SOURCE_NOT_CONFIGURED_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_STORED_SOURCE_ALL_TESTS))
def test_vectorSearch_stored_source(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: returnStoredSource behavior and errors."""
    coll = request.getfixturevalue(test_case.collection_fixture)
    result = execute_command(
        coll,
        {"aggregate": coll.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
