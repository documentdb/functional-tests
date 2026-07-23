"""Tests for the $vectorSearch stage: score similarity and range."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Gte,
    Len,
    Lte,
)
from documentdb_tests.framework.test_constants import (
    DOUBLE_ZERO,
)

from .utils.vectorSearch_common import (
    VectorSearchTest,
)

pytestmark = pytest.mark.requires(search=True)

# Property [Score Similarity Function]: the score is computed per the index
# similarity function, so cosine, euclidean, and dotProduct indexes each produce
# their own scores for the same data and query.
VECTORSEARCH_SCORE_SIMILARITY_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "similarity_cosine_scores",
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
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.9850712418556213)},
            {"_id": 3, "score": pytest.approx(0.9160251617431641)},
            {"_id": 4, "score": pytest.approx(0.6212677955627441)},
            {"_id": 5, "score": pytest.approx(0.5)},
        ],
        msg="$vectorSearch should produce cosine similarity scores for a cosine index",
    ),
    VectorSearchTest(
        "similarity_euclidean_scores",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "ve",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.9259259104728699)},
            {"_id": 3, "score": pytest.approx(0.7575758099555969)},
            {"_id": 4, "score": pytest.approx(0.4385964572429657)},
            {"_id": 5, "score": pytest.approx(0.3333333432674408)},
        ],
        msg="$vectorSearch should produce euclidean similarity scores for a euclidean index",
    ),
    VectorSearchTest(
        "similarity_dot_product_scores",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vd",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.8999999761581421)},
            {"_id": 3, "score": pytest.approx(0.800000011920929)},
            {"_id": 4, "score": pytest.approx(0.6000000238418579)},
            {"_id": 5, "score": pytest.approx(0.5)},
        ],
        msg="$vectorSearch should produce dotProduct similarity scores for a dotProduct index",
    ),
]

# Property [Score Filter Invariance]: a pre-filter narrows the candidate set but
# leaves a surviving document's vectorSearchScore identical to the unfiltered score.
VECTORSEARCH_SCORE_FILTER_INVARIANCE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "filter_preserves_surviving_scores",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 5,
                    "filter": {"cat": "x"},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected=[
            {"_id": 1, "score": pytest.approx(1.0)},
            {"_id": 2, "score": pytest.approx(0.9850712418556213)},
        ],
        msg="$vectorSearch should keep a surviving document's score identical under a filter",
    ),
]

# Property [searchScore Omitted]: requesting the unpopulated metadata name
# searchScore omits the projected field rather than erroring or populating it,
# because $vectorSearch populates vectorSearchScore, not searchScore.
VECTORSEARCH_SEARCHSCORE_OMITTED_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "search_score_metadata_omitted",
        pipeline=[
            {
                "$vectorSearch": {
                    "index": "vs_core_index",
                    "path": "vc",
                    "queryVector": [1.0, DOUBLE_ZERO, DOUBLE_ZERO],
                    "numCandidates": 10,
                    "limit": 2,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "searchScore"}}},
        ],
        expected=[{"_id": 1}, {"_id": 2}],
        msg="$vectorSearch should omit the searchScore field rather than error or populate it",
    ),
]

# Property [Score Range]: every returned document is assigned a vectorSearchScore
# that falls within the closed interval [0, 1].
VECTORSEARCH_SCORE_RANGE_TESTS: list[VectorSearchTest] = [
    VectorSearchTest(
        "score_range_within_unit_interval",
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
            {"$project": {"_id": 0, "score": {"$meta": "vectorSearchScore"}}},
        ],
        expected={
            "cursor.firstBatch": Len(5),
            "cursor.firstBatch.0.score": [Gte(0), Lte(1)],
            "cursor.firstBatch.1.score": [Gte(0), Lte(1)],
            "cursor.firstBatch.2.score": [Gte(0), Lte(1)],
            "cursor.firstBatch.3.score": [Gte(0), Lte(1)],
            "cursor.firstBatch.4.score": [Gte(0), Lte(1)],
        },
        msg="$vectorSearch should assign every result a score within [0, 1]",
    ),
]

VECTORSEARCH_SCORING_ALL_TESTS = (
    VECTORSEARCH_SCORE_SIMILARITY_TESTS
    + VECTORSEARCH_SCORE_FILTER_INVARIANCE_TESTS
    + VECTORSEARCH_SEARCHSCORE_OMITTED_TESTS
    + VECTORSEARCH_SCORE_RANGE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(VECTORSEARCH_SCORING_ALL_TESTS))
def test_vectorSearch_scoring(test_case: VectorSearchTest, engine_client, request):
    """$vectorSearch: score similarity and range."""
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
