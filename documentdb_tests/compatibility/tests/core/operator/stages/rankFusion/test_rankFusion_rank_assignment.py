"""Tests for how $rankFusion assigns a 1-based rank within an input pipeline."""

from __future__ import annotations

import pytest

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

# Property [Rank From Final Stage]: rank within an input pipeline is the
# document's 1-based position in the pipeline's final output, so stages after
# the ranking sort that reorder or drop documents change which documents are
# ranked and the rank each one receives.
RANKFUSION_RANK_FINAL_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "rank_last_sort_wins",
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
                            "p1": [{"$sort": {"a": -1}}, {"$sort": {"b": -1}}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 3, "score": rrf_score(2)},
            {"_id": 1, "score": rrf_score(3)},
        ],
        msg="$rankFusion should rank by the last $sort when a pipeline has two sorts",
    ),
    StageTestCase(
        "rank_skip_restarts_at_one",
        docs=[{"_id": 1, "a": 30}, {"_id": 2, "a": 20}, {"_id": 3, "a": 10}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}, {"$skip": 1}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 3, "score": rrf_score(2)},
        ],
        msg="$rankFusion should restart rank numbering at 1 after a $skip",
    ),
    StageTestCase(
        "rank_limit_truncates_after_ranking",
        docs=[{"_id": 1, "a": 30}, {"_id": 2, "a": 20}, {"_id": 3, "a": 10}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}, {"$limit": 2}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 1, "score": rrf_score(1)},
            {"_id": 2, "score": rrf_score(2)},
        ],
        msg="$rankFusion should keep ranks unchanged when a $limit truncates the output",
    ),
    StageTestCase(
        "rank_skip_then_limit",
        docs=[
            {"_id": 1, "a": 40},
            {"_id": 2, "a": 30},
            {"_id": 3, "a": 20},
            {"_id": 4, "a": 10},
        ],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}, {"$skip": 1}, {"$limit": 2}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 3, "score": rrf_score(2)},
        ],
        msg="$rankFusion should number ranks on the post-skip/limit output",
    ),
]

# Property [Competition Ranking]: documents whose sort keys compare equal
# (including a missing value and an explicit null, which sort as equal) receive
# the same 1-based rank with the next rank jumping by the tie-group size,
# yielding equal score contributions.
RANKFUSION_RANK_TIES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "rank_competition_tie_jumps",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 10}, {"_id": 3, "a": 5}],
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
            {"_id": 3, "score": rrf_score(3)},
        ],
        msg="$rankFusion should give tied sort keys equal rank and jump the next rank by tie size",
    ),
    StageTestCase(
        "rank_null_and_missing_tie",
        docs=[{"_id": 1, "a": 5}, {"_id": 2, "a": None}, {"_id": 3}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": 1}}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 2, "score": rrf_score(1)},
            {"_id": 3, "score": rrf_score(1)},
            {"_id": 1, "score": rrf_score(3)},
        ],
        msg="$rankFusion should treat a missing sort value and an explicit null as equal sort keys",
    ),
]

# Property [Rank After Sampling]: when an input pipeline ends with $sample, rank
# is assigned over the sampled documents, so the surviving documents receive
# ranks 1..k.
RANKFUSION_RANK_SAMPLE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "rank_sample_last_stage",
        docs=[{"_id": i, "a": 100 - i} for i in range(1, 6)],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}, {"$sample": {"size": 2}}],
                        }
                    },
                }
            },
            {"$project": {"_id": 0, "score": {"$meta": "score"}}},
        ],
        expected=[{"score": rrf_score(1)}, {"score": rrf_score(2)}],
        msg="$rankFusion should rank the documents emitted by $sample",
    ),
]

RANKFUSION_RANK_ASSIGNMENT_TESTS = (
    RANKFUSION_RANK_FINAL_STAGE_TESTS + RANKFUSION_RANK_TIES_TESTS + RANKFUSION_RANK_SAMPLE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_RANK_ASSIGNMENT_TESTS))
def test_rankFusion_rank_assignment(collection, test_case: StageTestCase):
    """Test how $rankFusion assigns a 1-based rank within an input pipeline."""
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
