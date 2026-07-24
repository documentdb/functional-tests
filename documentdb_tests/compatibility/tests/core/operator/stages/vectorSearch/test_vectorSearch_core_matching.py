"""Tests for the $vectorSearch stage: core matching and result semantics."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Eq,
    Len,
    NotExists,
)
from documentdb_tests.framework.test_constants import (
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [Result Cardinality At Most Limit]: when fewer documents match than
# limit, all available documents are returned with no error and no padding.
VECTORSEARCH_CARDINALITY_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "limit_exceeds_collection_returns_all",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 100,
                    "limit": 100,
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
        msg="$vectorSearch should return all available documents without padding when "
        "limit exceeds the collection size",
    ),
]

# Property [Full Document Shape]: by default the stage returns the complete source
# document with its fields intact and no injected similarity-score field.
VECTORSEARCH_FULL_DOCUMENT_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "full_document_returned",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 1,
                }
            },
        ],
        expected={
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0._id": Eq(1),
            "cursor.firstBatch.0.cat": Eq("x"),
            "cursor.firstBatch.0.year": Eq(1999),
            "cursor.firstBatch.0.name": Eq("a"),
            "cursor.firstBatch.0.vc": Eq([1.0, DOUBLE_ZERO, DOUBLE_ZERO]),
            "cursor.firstBatch.0.vectorSearchScore": NotExists(),
            "cursor.firstBatch.0.score": NotExists(),
        },
        msg="$vectorSearch should return the full source document with no injected "
        "score field by default",
    ),
]

# Property [Missing Collection Tolerance]: a well-formed query against a
# nonexistent collection, or an existing empty collection with no index, returns
# zero results with no namespace or index error.
VECTORSEARCH_MISSING_COLLECTION_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "nonexistent_collection_zero_results",
        collection_fixture="vector_search_absent_collection",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch should return zero results with no error against a "
        "nonexistent collection",
    ),
    VectorSearchTest(
        "empty_collection_zero_results",
        collection_fixture="vector_search_no_index_collection",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch should return zero results with no error against an empty "
        "collection that has no index",
    ),
]

VECTORSEARCH_CORE_MATCHING_ALL_TESTS = (
    VECTORSEARCH_CARDINALITY_TESTS
    + VECTORSEARCH_FULL_DOCUMENT_TESTS
    + VECTORSEARCH_MISSING_COLLECTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_CORE_MATCHING_ALL_TESTS))
def test_vectorSearch_core_matching(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: core matching and result semantics."""
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
