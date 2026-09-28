"""Tests for the $vectorSearch stage: stage-level acceptance and errors."""

from __future__ import annotations

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
    QUERY_METADATA_NOT_AVAILABLE_ERROR,
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

# Property [quantization Silently Ignored]: quantization is accepted with no
# validation regardless of value or BSON type and produces results identical to
# omitting it, never surfacing a value or type error.
VECTORSEARCH_QUANTIZATION_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"quantization_{tid}",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "quantization": value,
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
        msg=f"$vectorSearch should silently ignore a {tid} quantization value and "
        "return the same results as omitting it",
    )
    for tid, value in [
        ("scalar", "scalar"),
        ("bogus", "bogus"),
        ("int32", 1),
        ("int64", Int64(2)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", [1]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("5a9427648b0beebeb69537a5")),
        ("datetime", datetime(2020, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("null", None),
    ]
]

# Property [Unknown Spec Field Silently Ignored]: an unrecognized top-level spec
# field alongside all required fields is silently ignored and the query succeeds
# with results identical to omitting it, rather than raising an unknown-field error.
VECTORSEARCH_UNKNOWN_FIELD_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "unknown_field_ignored",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "bogus": 1,
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
        msg="$vectorSearch should silently ignore an unrecognized top-level spec "
        "field and return the same results as omitting it",
    ),
]

# Property [model/query Mutual Exclusivity]: model or query supplied alongside
# queryVector is rejected, because model is autoEmbed-only and exactly one of
# query and queryVector may be present, while both fields are still recognized by
# the parser.
VECTORSEARCH_MODEL_QUERY_EXCLUSIVITY_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "model_with_query_vector",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "model": "voyage-3",
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject model supplied alongside queryVector",
    ),
    VectorSearchTest(
        "query_with_query_vector",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "query": {"text": "hello"},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$vectorSearch should reject query supplied alongside queryVector",
    ),
]

# Property [Score Metadata Unavailable]: requesting metadata that $vectorSearch
# does not produce (textScore) in a following $project fails, because the stage
# populates vectorSearchScore, not text-score metadata.
VECTORSEARCH_SCORE_METADATA_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "score_metadata_text_score_unavailable",
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
            {"$project": {"_id": 1, "score": {"$meta": "textScore"}}},
        ],
        error_code=QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg="$vectorSearch should not provide text-score metadata for a following $meta textScore",
    ),
]

VECTORSEARCH_STAGE_BASICS_ALL_TESTS = (
    VECTORSEARCH_QUANTIZATION_TESTS
    + VECTORSEARCH_UNKNOWN_FIELD_TESTS
    + VECTORSEARCH_MODEL_QUERY_EXCLUSIVITY_ERROR_TESTS
    + VECTORSEARCH_SCORE_METADATA_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_STAGE_BASICS_ALL_TESTS))
def test_vectorSearch_stage_basics(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: stage-level acceptance and errors."""
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
