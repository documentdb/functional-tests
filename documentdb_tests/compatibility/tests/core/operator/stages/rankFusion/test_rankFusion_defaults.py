"""Tests for $rankFusion defaulting and null handling of optional fields."""

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

# Property [Null combination]: a null combination is accepted and behaves as if
# omitted, so every pipeline uses the default weight 1.
RANKFUSION_NULL_COMBINATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_combination_default_weight",
        docs=[{"_id": 1, "a": 10, "b": 1}, {"_id": 2, "a": 5, "b": 2}, {"_id": 3, "a": 1, "b": 3}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "combination": None,
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 1, "score": rrf_score(1, 3)},
            {"_id": 3, "score": rrf_score(1, 3)},
            {"_id": 2, "score": rrf_score(2, 2)},
        ],
        msg="$rankFusion should accept a null combination and apply the default weight 1",
    ),
]

# Property [Null scoreDetails]: a null scoreDetails is accepted and treated as
# false, so the stage runs and returns the ranked documents.
RANKFUSION_NULL_SCORE_DETAILS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_score_details_accepted",
        docs=[{"_id": 1, "a": 10, "b": 1}, {"_id": 2, "a": 5, "b": 2}, {"_id": 3, "a": 1, "b": 3}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "scoreDetails": None,
                }
            }
        ],
        expected=[
            {"_id": 1, "a": 10, "b": 1},
            {"_id": 3, "a": 1, "b": 3},
            {"_id": 2, "a": 5, "b": 2},
        ],
        msg="$rankFusion should accept a null scoreDetails and treat it as false",
    ),
]

# Property [Default Values]: a pipeline absent from combination.weights takes
# the default weight 1.
RANKFUSION_DEFAULT_VALUES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "default_omitted_combination",
        docs=[{"_id": 1, "a": 10, "b": 1}, {"_id": 2, "a": 5, "b": 2}, {"_id": 3, "a": 1, "b": 3}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 1, "score": rrf_score(1, 3)},
            {"_id": 3, "score": rrf_score(1, 3)},
            {"_id": 2, "score": rrf_score(2, 2)},
        ],
        msg="$rankFusion should apply weight 1 to every pipeline when combination is omitted",
    ),
    StageTestCase(
        "default_empty_weights",
        docs=[{"_id": 1, "a": 10, "b": 1}, {"_id": 2, "a": 5, "b": 2}, {"_id": 3, "a": 1, "b": 3}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "combination": {"weights": {}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 1, "score": rrf_score(1, 3)},
            {"_id": 3, "score": rrf_score(1, 3)},
            {"_id": 2, "score": rrf_score(2, 2)},
        ],
        msg="$rankFusion should apply weight 1 to every pipeline when weights map is empty",
    ),
    StageTestCase(
        "default_partial_weights",
        docs=[{"_id": 1, "a": 10, "b": 1}, {"_id": 2, "a": 5, "b": 2}, {"_id": 3, "a": 1, "b": 3}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "p1": [{"$sort": {"a": -1}}],
                            "p2": [{"$sort": {"b": -1}}],
                        }
                    },
                    "combination": {"weights": {"p1": 2}},
                }
            },
            {"$project": {"_id": 1, "score": {"$meta": "score"}}},
        ],
        expected=[
            {"_id": 1, "score": rrf_score(1, 3, weights=(2, 1))},
            {"_id": 2, "score": rrf_score(2, 2, weights=(2, 1))},
            {"_id": 3, "score": rrf_score(3, 1, weights=(2, 1))},
        ],
        msg="$rankFusion should apply weight 1 to a pipeline omitted from a partial weights map",
    ),
]

RANKFUSION_DEFAULTS_TESTS = (
    RANKFUSION_NULL_COMBINATION_TESTS
    + RANKFUSION_NULL_SCORE_DETAILS_TESTS
    + RANKFUSION_DEFAULT_VALUES_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_DEFAULTS_TESTS))
def test_rankFusion_defaults(collection, test_case: StageTestCase):
    """Test $rankFusion defaulting and null handling of optional fields."""
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
