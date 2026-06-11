"""Tests for $rankFusion pipeline position constraints and container placement."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    RANK_FUSION_NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Top-Level Stage Position]: $rankFusion is rejected anywhere other
# than the first stage of the top-level pipeline, whether an ordinary stage
# precedes it or a second $rankFusion follows the first.
RANKFUSION_TOP_LEVEL_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "position_after_match",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {"$match": {"a": {"$gte": 1}}},
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
        ],
        error_code=RANK_FUSION_NOT_FIRST_STAGE_ERROR,
        msg="$rankFusion should reject being used after a preceding stage",
    ),
    StageTestCase(
        "position_second_rank_fusion",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
            {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
        ],
        error_code=RANK_FUSION_NOT_FIRST_STAGE_ERROR,
        msg="$rankFusion should reject a second $rankFusion stage in the pipeline",
    ),
]

# Property [Facet Sub-Pipeline Position]: $rankFusion is accepted as the first
# stage of a $facet sub-pipeline and returns its ranked documents there, but is
# rejected with the not-first-stage error when another stage precedes it inside
# the same $facet sub-pipeline.
RANKFUSION_FACET_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_first_stage",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        pipeline=[
            {
                "$facet": {
                    "ranked": [
                        {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}
                    ]
                }
            }
        ],
        expected=[{"ranked": [{"_id": 2, "a": 2}, {"_id": 1, "a": 1}]}],
        msg="$rankFusion should run as the first stage of a $facet sub-pipeline",
    ),
    StageTestCase(
        "facet_not_first_stage",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$facet": {
                    "ranked": [
                        {"$match": {"a": 1}},
                        {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}},
                    ]
                }
            }
        ],
        error_code=RANK_FUSION_NOT_FIRST_STAGE_ERROR,
        msg="$rankFusion should reject being preceded by a stage inside a $facet sub-pipeline",
    ),
]

RANKFUSION_POSITION_TESTS = RANKFUSION_TOP_LEVEL_POSITION_TESTS + RANKFUSION_FACET_POSITION_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_POSITION_TESTS))
def test_rankFusion_position_cases(collection, test_case: StageTestCase):
    """Test $rankFusion pipeline position constraints."""
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


# Property [Lookup First-Stage Acceptance]: $rankFusion is accepted as the first
# stage of a $lookup sub-pipeline and returns its ranked documents there. This
# case self-references the fixture collection, so the pipeline is built with its
# runtime name rather than declared as static data.
@pytest.mark.aggregate
def test_rankFusion_first_stage_in_lookup_subpipeline(collection):
    """Test $rankFusion accepted as the first stage of a $lookup sub-pipeline."""
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}])
    rank_fusion = {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}
    pipeline = [
        {"$lookup": {"from": collection.name, "pipeline": [rank_fusion], "as": "joined"}},
        {"$sort": {"_id": 1}},
    ]
    expected = [
        {"_id": 1, "a": 1, "joined": [{"_id": 2, "a": 2}, {"_id": 1, "a": 1}]},
        {"_id": 2, "a": 2, "joined": [{"_id": 2, "a": 2}, {"_id": 1, "a": 1}]},
    ]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=expected,
        msg="$rankFusion should run as the first stage of a 'lookup' sub-pipeline",
    )


# Property [UnionWith First-Stage Acceptance]: $rankFusion is accepted as the
# first stage of a $unionWith sub-pipeline and returns its ranked documents
# there. This case self-references the fixture collection, so the pipeline is
# built with its runtime name rather than declared as static data.
@pytest.mark.aggregate
def test_rankFusion_first_stage_in_unionWith_subpipeline(collection):
    """Test $rankFusion accepted as the first stage of a $unionWith sub-pipeline."""
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}])
    rank_fusion = {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}
    pipeline = [
        {"$unionWith": {"coll": collection.name, "pipeline": [rank_fusion]}},
        {"$sort": {"_id": 1}},
    ]
    expected = [
        {"_id": 1, "a": 1},
        {"_id": 1, "a": 1},
        {"_id": 2, "a": 2},
        {"_id": 2, "a": 2},
    ]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=expected,
        msg="$rankFusion should run as the first stage of a 'unionWith' sub-pipeline",
    )


# Property [Lookup Not-First Rejection]: $rankFusion is rejected with the
# not-first-stage error when another stage precedes it inside a $lookup
# sub-pipeline.
@pytest.mark.aggregate
def test_rankFusion_not_first_in_lookup_subpipeline(collection):
    """Test $rankFusion rejected when preceded by a stage in a $lookup sub-pipeline."""
    collection.insert_many([{"_id": 1, "a": 1}])
    rank_fusion = {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}
    pipeline = [
        {
            "$lookup": {
                "from": collection.name,
                "pipeline": [{"$match": {"a": 1}}, rank_fusion],
                "as": "joined",
            }
        }
    ]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(
        result,
        error_code=RANK_FUSION_NOT_FIRST_STAGE_ERROR,
        msg="$rankFusion should reject being preceded by a stage in a 'lookup' sub-pipeline",
    )


# Property [UnionWith Not-First Rejection]: $rankFusion is rejected with the
# not-first-stage error when another stage precedes it inside a $unionWith
# sub-pipeline.
@pytest.mark.aggregate
def test_rankFusion_not_first_in_unionWith_subpipeline(collection):
    """Test $rankFusion rejected when preceded by a stage in a $unionWith sub-pipeline."""
    collection.insert_many([{"_id": 1, "a": 1}])
    rank_fusion = {"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}
    pipeline = [
        {
            "$unionWith": {
                "coll": collection.name,
                "pipeline": [{"$match": {"a": 1}}, rank_fusion],
            }
        }
    ]
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    assertResult(
        result,
        error_code=RANK_FUSION_NOT_FIRST_STAGE_ERROR,
        msg="$rankFusion should reject being preceded by a stage in a 'unionWith' sub-pipeline",
    )


# Property [Database Scope]: $rankFusion run at database scope (aggregate: 1)
# rather than against a single collection produces an invalid-namespace error.
@pytest.mark.aggregate
def test_rankFusion_database_scope(collection):
    """Test $rankFusion rejected when run at database scope."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [{"$rankFusion": {"input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}],
            "cursor": {},
        },
    )
    assertResult(
        result,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$rankFusion should reject running at database scope instead of a collection",
    )
