"""Tests for $rankFusion score computation and result ordering."""

from __future__ import annotations

import pytest
from bson import ObjectId

from documentdb_tests.compatibility.tests.core.operator.stages.rankFusion.utils.rankFusion_common import (  # noqa: E501
    rrf_score,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [RRF Scoring and Result Ordering]: each output document's score
# metadata equals the sum over every pipeline that returned it of
# weight / (60 + rank) (rank is 1-based), and results are ordered
# by that score descending; a document returned by more than one pipeline
# appears exactly once in the output with its per-pipeline contributions summed.
RANKFUSION_RRF_SCORING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "rrf_score_and_descending_order",
        docs=[
            {"_id": 1, "a": 30, "b": 10},
            {"_id": 2, "a": 20, "b": 30},
            {"_id": 3, "a": 10, "b": 20},
        ],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "combination": {"weights": {"p1": 1, "p2": 1}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(2, 1)},
            {"_id": 1, "score": rrf_score(1, 3)},
            {"_id": 3, "score": rrf_score(3, 2)},
        ],
        msg="$rankFusion should sum weight/(60+rank) per pipeline and order by score descending",
    ),
    StageTestCase(
        "rrf_score_increases_with_more_pipelines",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$match": {"_id": 1}}, {"$sort": {"a": -1}}],
                            "p2": [{"$match": {"_id": 1}}, {"$sort": {"a": -1}}],
                            "p3": [{"$match": {"_id": 2}}, {"$sort": {"a": -1}}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 1, "score": rrf_score(1, weights=(2,))},
            {"_id": 2, "score": rrf_score(1)},
        ],
        msg="$rankFusion should rank a document in two pipelines above one in a single pipeline",
    ),
    StageTestCase(
        "rrf_weight_scales_contribution",
        docs=[
            {"_id": 1, "a": 30, "b": 10},
            {"_id": 2, "a": 20, "b": 30},
            {"_id": 3, "a": 10, "b": 20},
        ],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "combination": {"weights": {"p1": 2, "p2": 1}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 1, "score": rrf_score(1, 3, weights=(2, 1))},
            {"_id": 2, "score": rrf_score(2, 1, weights=(2, 1))},
            {"_id": 3, "score": rrf_score(3, 2, weights=(2, 1))},
        ],
        msg="$rankFusion should scale a pipeline's contribution linearly with its weight",
    ),
    StageTestCase(
        "rrf_zero_weight_contributes_nothing",
        docs=[
            {"_id": 1, "a": 30, "b": 10},
            {"_id": 2, "a": 20, "b": 30},
            {"_id": 3, "a": 10, "b": 20},
        ],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "combination": {"weights": {"p1": 0}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 3, "score": rrf_score(2)},
            {"_id": 1, "score": rrf_score(3)},
        ],
        msg="$rankFusion should let a zero-weight pipeline contribute nothing to the score",
    ),
]

# Property [Tie-Breaking]: output documents with equal RRF scores are ordered
# by _id ascending, independent of insertion order.
RANKFUSION_TIE_BREAKING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "tie_break_numeric_id",
        docs=[{"_id": 3, "a": 10}, {"_id": 1, "a": 10}, {"_id": 2, "a": 10}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 1, "score": rrf_score(1)},
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 3, "score": rrf_score(1)},
        ],
        msg="$rankFusion should break score ties by numeric _id ascending, not insertion order",
    ),
    StageTestCase(
        "tie_break_string_id",
        docs=[{"_id": "c", "a": 10}, {"_id": "a", "a": 10}, {"_id": "b", "a": 10}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": "a", "score": rrf_score(1)},
            {"_id": "b", "score": rrf_score(1)},
            {"_id": "c", "score": rrf_score(1)},
        ],
        msg="$rankFusion should break score ties by string _id ascending, not insertion order",
    ),
    StageTestCase(
        "tie_break_objectid_id",
        docs=[
            {"_id": ObjectId("000000000000000000000003"), "a": 10},
            {"_id": ObjectId("000000000000000000000001"), "a": 10},
            {"_id": ObjectId("000000000000000000000002"), "a": 10},
        ],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": ObjectId("000000000000000000000001"), "score": rrf_score(1)},
            {"_id": ObjectId("000000000000000000000002"), "score": rrf_score(1)},
            {"_id": ObjectId("000000000000000000000003"), "score": rrf_score(1)},
        ],
        msg="$rankFusion should break score ties by ObjectId _id ascending, not insertion order",
    ),
]

RANKFUSION_SCORING_TESTS = RANKFUSION_RRF_SCORING_TESTS + RANKFUSION_TIE_BREAKING_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_SCORING_TESTS))
def test_rankFusion_scoring(collection, test_case: StageTestCase):
    """Test $rankFusion score computation and result ordering."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
