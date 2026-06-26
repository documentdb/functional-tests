"""Tests for the $vectorSearch stage: nestedRoot scoping and nestedOptions."""

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
    Contains,
    Len,
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

_NESTED_CORPUS = [
    {
        "_id": 1,
        "country": "US",
        "reviews": [
            {"rating": 5, "embedding": [1.0, DOUBLE_ZERO, DOUBLE_ZERO]},
            {"rating": 3, "embedding": [0.9, 0.1, DOUBLE_ZERO]},
        ],
    },
    {
        "_id": 2,
        "country": "US",
        "reviews": [{"rating": 2, "embedding": [DOUBLE_ZERO, 1.0, DOUBLE_ZERO]}],
    },
    {
        "_id": 3,
        "country": "CA",
        "reviews": [{"rating": 5, "embedding": [0.8, 0.2, DOUBLE_ZERO]}],
    },
]


@pytest.fixture(scope="module")
def nested_vector_search_collection(engine_client, worker_id):
    """Provide a collection with a READY nestedRoot vectorSearch index over a fixed corpus."""
    db_name = f"vs_nested_{worker_id}"
    db = engine_client[db_name]
    coll = db["nested_vectors"]
    db.drop_collection(coll.name)
    db.create_collection(coll.name)
    coll.insert_many([dict(doc) for doc in _NESTED_CORPUS])
    db.command(
        {
            "createSearchIndexes": coll.name,
            "indexes": [
                {
                    "name": "vs_nested_index",
                    "type": "vectorSearch",
                    "definition": {
                        "nestedRoot": "reviews",
                        "fields": [
                            {
                                "type": "vector",
                                "path": "reviews.embedding",
                                "numDimensions": 3,
                                "similarity": "cosine",
                            },
                            {"type": "filter", "path": "reviews.rating"},
                            {"type": "filter", "path": "country"},
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
        raise TimeoutError("nestedRoot vectorSearch index did not reach READY state")
    yield coll
    engine_client.drop_database(db_name)


# Property [parentFilter Nested Root Scoping]: on a nestedRoot index parentFilter
# pre-filters root-level fields while filter pre-filters nested-level fields, the
# two AND-combine, and a predicate referencing the other level returns zero results.
VECTORSEARCH_PARENT_FILTER_NESTED_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "nested_parent_filter_root_field",
        collection_fixture="nested_vector_search_collection",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "parentFilter": {"country": "US"},
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$vectorSearch parentFilter should pre-filter root-level fields on a nestedRoot index",
    ),
    VectorSearchTest(
        "nested_filter_nested_field",
        collection_fixture="nested_vector_search_collection",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "filter": {"reviews.rating": 5},
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 3)]},
        msg="$vectorSearch filter should pre-filter nested-level fields on a nestedRoot index",
    ),
    VectorSearchTest(
        "nested_filter_and_parent_filter",
        collection_fixture="nested_vector_search_collection",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "filter": {"reviews.rating": 5},
                    "parentFilter": {"country": "US"},
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(1), Contains("_id", 1)]},
        msg="$vectorSearch should AND-combine nested filter with root parentFilter",
    ),
    VectorSearchTest(
        "nested_parent_filter_on_nested_field",
        collection_fixture="nested_vector_search_collection",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "parentFilter": {"reviews.rating": 5},
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch parentFilter on a nested field should return zero results",
    ),
    VectorSearchTest(
        "nested_filter_on_root_field",
        collection_fixture="nested_vector_search_collection",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "filter": {"country": "US"},
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch filter on a root field should return zero results",
    ),
]

# Property [nestedOptions scoreMode]: on a nestedRoot index nestedOptions.scoreMode
# combines a parent's matching nested-array child scores, with "avg" averaging the
# child scores and "max" taking the maximum.
VECTORSEARCH_NESTED_OPTIONS_SCORE_MODE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "score_mode_avg",
        collection_fixture="nested_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "nestedOptions": {"scoreMode": "avg"},
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(0.9984709024429321)},
            {"_id": 2, "score": pytest.approx(0.5)},
            {"_id": 3, "score": pytest.approx(0.9850712418556213)},
        ],
        msg="$vectorSearch should average a parent's matching child scores for scoreMode avg",
    ),
    VectorSearchTest(
        "score_mode_max",
        collection_fixture="nested_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "nestedOptions": {"scoreMode": "max"},
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.5)},
            {"_id": 3, "score": pytest.approx(0.9850712418556213)},
        ],
        msg="$vectorSearch should take the maximum of a parent's matching child "
        "scores for scoreMode max",
    ),
]

# Property [nestedOptions Default Max]: omitting nestedOptions, or providing an
# empty nestedOptions document, yields the same parent score as scoreMode "max".
VECTORSEARCH_NESTED_OPTIONS_DEFAULT_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "default_max_omitted",
        collection_fixture="nested_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.5)},
            {"_id": 3, "score": pytest.approx(0.9850712418556213)},
        ],
        msg="$vectorSearch should default to scoreMode max when nestedOptions is omitted",
    ),
    VectorSearchTest(
        "default_max_empty_document",
        collection_fixture="nested_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "nestedOptions": {},
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.5)},
            {"_id": 3, "score": pytest.approx(0.9850712418556213)},
        ],
        msg="$vectorSearch should default to scoreMode max for an empty nestedOptions document",
    ),
    VectorSearchTest(
        "default_max_score_mode_null",
        collection_fixture="nested_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 20,
                    "limit": 5,
                    "nestedOptions": {"scoreMode": None},
                }
            },
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.5)},
            {"_id": 3, "score": pytest.approx(0.9850712418556213)},
        ],
        msg="$vectorSearch should treat a null scoreMode as absent and default to scoreMode max",
    ),
]

# Property [nestedOptions Non-Object Rejection]: a nestedOptions value that is
# not a document is rejected as not a document, with no type coercion.
VECTORSEARCH_NESTED_OPTIONS_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"nested_options_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "nestedOptions": val,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} nestedOptions value as not a document",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", []),
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

# Property [nestedOptions Null As Omitted]: nestedOptions null is treated as
# field-absent and the query succeeds on a flat index as if nestedOptions were
# omitted, in contrast to an empty nestedOptions document, which is rejected on a
# flat index for lacking a nested root.
VECTORSEARCH_NESTED_OPTIONS_NULL_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "nested_options_null_omitted_flat_index",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "nestedOptions": None,
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(5),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
                Contains("_id", 4),
                Contains("_id", 5),
            ]
        },
        msg="$vectorSearch should treat nestedOptions null as omitted and succeed on a "
        "flat index",
    ),
]

# Property [nestedOptions Requires Nested Root]: nestedOptions on a flat
# (non-nestedRoot) index is rejected because the index has no nested root for a
# nested-array score mode to apply to.
VECTORSEARCH_NESTED_OPTIONS_FLAT_INDEX_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "nested_options_on_flat_index",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "nestedOptions": {"scoreMode": "avg"},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject nestedOptions on a flat index lacking a nested root",
    ),
]

# Property [nestedOptions Invalid scoreMode]: a scoreMode outside the accepted
# set is rejected, and the accepted values are matched case-sensitively.
VECTORSEARCH_NESTED_OPTIONS_SCORE_MODE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"nested_options_score_mode_{tid}",
        collection_fixture="nested_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "nestedOptions": {"scoreMode": score_mode},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject the {tid} scoreMode as unsupported",
    )
    for tid, score_mode in [
        ("unrecognized", "median"),
        ("case_variant", "AVG"),
    ]
]

# Property [nestedOptions scoreMode Type Strictness]: a non-string scoreMode value
# of any BSON type is rejected as not a string with no coercion.
VECTORSEARCH_NESTED_OPTIONS_SCORE_MODE_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"nested_options_score_mode_type_{tid}",
        collection_fixture="nested_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "nestedOptions": {"scoreMode": val},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} scoreMode value as a non-string",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", ["max"]),
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

# Property [nestedOptions Unknown Sub-Field Rejection]: an unrecognized sub-field
# of nestedOptions is rejected, unlike unknown top-level spec fields which are
# silently ignored.
VECTORSEARCH_NESTED_OPTIONS_UNKNOWN_SUBFIELD_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "nested_options_unknown_subfield",
        collection_fixture="nested_vector_search_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_nested_index",
                    "path": "reviews.embedding",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "nestedOptions": {"bogus": 1},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject an unrecognized nestedOptions sub-field",
    ),
]

VECTORSEARCH_NESTED_ALL_TESTS = (
    VECTORSEARCH_PARENT_FILTER_NESTED_TESTS
    + VECTORSEARCH_NESTED_OPTIONS_SCORE_MODE_TESTS
    + VECTORSEARCH_NESTED_OPTIONS_DEFAULT_TESTS
    + VECTORSEARCH_NESTED_OPTIONS_TYPE_ERROR_TESTS
    + VECTORSEARCH_NESTED_OPTIONS_NULL_TESTS
    + VECTORSEARCH_NESTED_OPTIONS_FLAT_INDEX_ERROR_TESTS
    + VECTORSEARCH_NESTED_OPTIONS_SCORE_MODE_ERROR_TESTS
    + VECTORSEARCH_NESTED_OPTIONS_SCORE_MODE_TYPE_ERROR_TESTS
    + VECTORSEARCH_NESTED_OPTIONS_UNKNOWN_SUBFIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_NESTED_ALL_TESTS))
def test_vectorSearch_nested(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: nestedRoot scoping and nestedOptions."""
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
        raw_res=test_case.raw_res,
    )
