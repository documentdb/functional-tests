"""Tests for the $vectorSearch stage: exact ANN/ENN selection."""

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
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
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

# Property [exact ANN Selection]: when exact is absent (omitted or null) or
# false, ANN runs with numCandidates and returns documents ordered by similarity
# up to limit.
VECTORSEARCH_EXACT_ANN_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "exact_omitted_defaults_ann",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 3,
                }
            },
        ],
        expected=PerDoc({"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}),
        msg="$vectorSearch should default to ANN and return similarity-ordered "
        "documents up to limit when exact is omitted",
    ),
    VectorSearchTest(
        "exact_false_ann",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": False,
                    "numCandidates": 10,
                    "limit": 3,
                }
            },
        ],
        expected=PerDoc({"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}),
        msg="$vectorSearch should run ANN and return similarity-ordered documents "
        "up to limit when exact is false",
    ),
    VectorSearchTest(
        "exact_null_treated_as_absent",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": None,
                    "numCandidates": 10,
                    "limit": 3,
                }
            },
        ],
        expected=PerDoc({"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}),
        msg="$vectorSearch should treat exact null as field-absent and apply ANN "
        "when numCandidates is present",
    ),
]

# Property [exact ENN Selection]: exact:true runs ENN and succeeds whether
# numCandidates is omitted or null, returning documents ordered by similarity up
# to limit.
VECTORSEARCH_EXACT_ENN_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "exact_true_num_candidates_omitted",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": True,
                    "limit": 3,
                }
            },
        ],
        expected=PerDoc({"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}),
        msg="$vectorSearch should run ENN without numCandidates and return "
        "similarity-ordered documents up to limit",
    ),
    VectorSearchTest(
        "exact_true_num_candidates_null",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": True,
                    "numCandidates": None,
                    "limit": 3,
                }
            },
        ],
        expected=PerDoc({"_id": Eq(1)}, {"_id": Eq(2)}, {"_id": Eq(3)}),
        msg="$vectorSearch should run ENN with numCandidates null and return "
        "similarity-ordered documents up to limit",
    ),
    VectorSearchTest(
        "exact_true_scores_match_ann",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": True,
                    "limit": 5,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.9850712418556213)},
            {"_id": 3, "score": pytest.approx(0.9160251617431641)},
            {"_id": 4, "score": pytest.approx(0.6212677955627441)},
            {"_id": 5, "score": pytest.approx(0.5)},
        ],
        msg="$vectorSearch ENN should return the same similarity-ordered ids and "
        "scores as the equivalent ANN query",
    ),
]

# Property [exact Type Strictness]: a non-boolean exact value of any BSON type is
# rejected as a non-boolean with no coercion of numeric or string truthiness.
VECTORSEARCH_EXACT_TYPE_ERROR_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        f"exact_type_{tid}",
        collection_fixture="vector_search_no_index_collection",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "exact": val,
                    "numCandidates": 10,
                    "limit": 5,
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$vectorSearch should reject a {tid} exact value as a non-boolean",
    )
    for tid, val in [
        ("int32_one", 1),
        ("int32_zero", 0),
        ("int64", Int64(1)),
        ("double_one", 1.0),
        ("double_zero", DOUBLE_ZERO),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("string_true", "true"),
        ("string_empty", ""),
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

VECTORSEARCH_EXACT_ALL_TESTS = (
    VECTORSEARCH_EXACT_ANN_TESTS
    + VECTORSEARCH_EXACT_ENN_TESTS
    + VECTORSEARCH_EXACT_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_EXACT_ALL_TESTS))
def test_vectorSearch_exact(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: exact ANN/ENN selection."""
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
