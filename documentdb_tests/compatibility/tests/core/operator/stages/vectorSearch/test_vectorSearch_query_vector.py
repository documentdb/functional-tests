"""Tests for the $vectorSearch stage: queryVector accepted forms."""

from __future__ import annotations

import pytest
from bson import (
    Int64,
)
from bson.binary import Binary, BinaryVectorDtype

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DOUBLE_ZERO,
    INT64_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Baseline cosine scores for the shared query vector, used to assert that every
# accepted numeric and float32-BinData query vector form scores identically.
_COSINE_QUERY_SCORES = [
    {"_id": 1, "score": pytest.approx(1.0)},
    {"_id": 2, "score": pytest.approx(0.9850712418556213)},
    {"_id": 3, "score": pytest.approx(0.9160251617431641)},
    {"_id": 4, "score": pytest.approx(0.6212677955627441)},
    {"_id": 5, "score": pytest.approx(0.5)},
]

# Property [queryVector Numeric And Float32 Equivalence]: every accepted numeric
# array form and the equivalent float32 BinData query vector yield scores
# identical to the double-array baseline.
VECTORSEARCH_QUERY_VECTOR_EQUIVALENCE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"qv_equivalence_{tid}",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": qv,
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=_COSINE_QUERY_SCORES,
        msg=f"$vectorSearch should accept a {tid} queryVector and score it "
        "identically to the double array",
    )
    for tid, qv in [
        ("int32_array", [1, 0, 0]),
        ("int64_array", [Int64(1), INT64_ZERO, INT64_ZERO]),
        ("mixed_array", [1, DOUBLE_ZERO, 0]),
        (
            "float32_bindata",
            Binary.from_vector([1.0, DOUBLE_ZERO, DOUBLE_ZERO], BinaryVectorDtype.FLOAT32),
        ),
    ]
]

# Property [queryVector Signed Components]: a query vector containing negative
# components is accepted by cosine, euclidean, and dotProduct indexes.
VECTORSEARCH_QUERY_VECTOR_SIGN_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"qv_mixed_sign_{tid}",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": path,
                    "queryVector": [0.5, -0.5, 0.5],
                    "numCandidates": 10,
                    "limit": 5,
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
        msg=f"$vectorSearch should accept a mixed-sign queryVector on a {tid} index",
    )
    for tid, path in [
        ("cosine", "vc"),
        ("euclidean", "ve"),
        ("dot_product", "vd"),
    ]
]

# Property [queryVector Float32 Narrowing]: a query vector whose elements narrow
# to a finite, nonzero float32 value is accepted and returns results.
VECTORSEARCH_QUERY_VECTOR_FLOAT32_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "qv_float32_max_boundary",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [3.4028235e38, DOUBLE_ZERO, 1.0],
                    "numCandidates": 10,
                    "limit": 5,
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
        msg="$vectorSearch should accept a queryVector component at the FLT_MAX boundary",
    ),
    VectorSearchTest(
        "qv_float32_underflow_nonzero",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1e-50, DOUBLE_ZERO, 1.0],
                    "numCandidates": 10,
                    "limit": 5,
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
        msg="$vectorSearch should accept a queryVector component that underflows to "
        "zero while the vector stays nonzero",
    ),
]

# Property [queryVector Zero Vector Acceptance]: a zero query vector ([0,0,0]) is
# accepted by euclidean and dotProduct indexes and returns results.
VECTORSEARCH_QUERY_VECTOR_ZERO_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"qv_zero_{tid}",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": path,
                    "queryVector": qv,
                    "numCandidates": 10,
                    "limit": 5,
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
        msg=f"$vectorSearch should accept a {tid} queryVector and return results",
    )
    for tid, path, qv in [
        ("all_euclidean", "ve", [DOUBLE_ZERO, DOUBLE_ZERO, DOUBLE_ZERO]),
        ("all_dot_product", "vd", [DOUBLE_ZERO, DOUBLE_ZERO, DOUBLE_ZERO]),
    ]
]

# Property [queryVector Subtype Mismatch Silent Miss]: a BinData query vector
# whose element subtype differs from the indexed float32 returns zero results
# with no error.
VECTORSEARCH_QUERY_VECTOR_SUBTYPE_MISS_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "qv_int8_subtype_cosine",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": Binary.from_vector([1, 0, 0], BinaryVectorDtype.INT8),
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch should silently return no results for an int8 BinData "
        "queryVector against a float32 cosine index",
    ),
    VectorSearchTest(
        "qv_int8_subtype_euclidean",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "ve",
                    "queryVector": Binary.from_vector([1, 0, 0], BinaryVectorDtype.INT8),
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch should silently return no results for an int8 BinData "
        "queryVector against a float32 euclidean index",
    ),
    VectorSearchTest(
        "qv_packed_bit_subtype_euclidean",
        raw_res=True,
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "v8",
                    "queryVector": Binary.from_vector(
                        [0b10110010], BinaryVectorDtype.PACKED_BIT, padding=0
                    ),
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
        ],
        expected={"cursor.firstBatch": Len(0)},
        msg="$vectorSearch should silently return no results for a packed_bit "
        "BinData queryVector against a float32 euclidean index",
    ),
]

VECTORSEARCH_QUERY_VECTOR_ALL_TESTS = (
    VECTORSEARCH_QUERY_VECTOR_EQUIVALENCE_TESTS
    + VECTORSEARCH_QUERY_VECTOR_SIGN_TESTS
    + VECTORSEARCH_QUERY_VECTOR_FLOAT32_TESTS
    + VECTORSEARCH_QUERY_VECTOR_ZERO_TESTS
    + VECTORSEARCH_QUERY_VECTOR_SUBTYPE_MISS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_QUERY_VECTOR_ALL_TESTS))
def test_vectorSearch_query_vector(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: queryVector accepted forms."""
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
