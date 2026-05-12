"""Tests for $collStats pipeline position requirements."""

from __future__ import annotations

import pytest
from bson.son import SON

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command


# Property [Stage Position Requirement - First With Downstream Stages]: $collStats
# as the first stage followed by other stages succeeds.
@pytest.mark.aggregate
def test_collStats_first_with_project(collection):
    """Test that $collStats followed by $project succeeds."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$collStats": {"count": {}}},
                {"$project": {"_id": 0, "count": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"count": 1}],
        msg="$collStats followed by $project should succeed",
    )


# Property [Stage Position Requirement - Not First Error]: $collStats must be
# the first stage in the main aggregation pipeline; placing it at any other
# position produces NOT_FIRST_STAGE_ERROR.
@pytest.mark.aggregate
def test_collStats_not_first_stage_error(collection):
    """Test that $collStats not as the first stage produces an error."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {}}, {"$collStats": {}}],
            "cursor": {},
        },
    )
    assertFailureCode(result, NOT_FIRST_STAGE_ERROR, msg="not first stage")


# Property [Stage Position Requirement - Sub-Pipeline Allowed]: $collStats is
# allowed as the first stage in $lookup and $unionWith sub-pipelines because
# the first-stage restriction applies per-pipeline.
@pytest.mark.aggregate
def test_collStats_allowed_in_lookup_sub_pipeline(collection):
    """Test that $collStats works as first stage in $lookup sub-pipeline."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": collection.name,
                        "pipeline": [
                            {"$collStats": {"count": {}}},
                            {"$project": {"_id": 0, "count": "$count"}},
                        ],
                        "as": "stats",
                    }
                },
                {"$project": {"_id": 0, "stats_count": {"$arrayElemAt": ["$stats.count", 0]}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"stats_count": 1}],
        msg="$collStats should work as first stage in $lookup sub-pipeline",
    )


@pytest.mark.aggregate
def test_collStats_allowed_in_unionwith_sub_pipeline(collection):
    """Test that $collStats works as first stage in $unionWith sub-pipeline."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$collStats": {"count": {}}},
                {"$project": {"_id": 0, "count": "$count"}},
                {
                    "$unionWith": {
                        "coll": collection.name,
                        "pipeline": [
                            {"$collStats": {"count": {}}},
                            {"$project": {"_id": 0, "count": "$count"}},
                        ],
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"count": 1}, {"count": 1}],
        msg="$collStats should work as first stage in $unionWith sub-pipeline",
    )


# Property [Stage Position Requirement - Not First In Sub-Pipeline]: $collStats
# must also be the first stage in $lookup and $unionWith sub-pipelines.
@pytest.mark.aggregate
def test_collStats_not_first_in_lookup_sub_pipeline(collection):
    """Test that $collStats not first in $lookup sub-pipeline produces an error."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": collection.name,
                        "pipeline": [
                            {"$match": {}},
                            {"$collStats": {"count": {}}},
                        ],
                        "as": "stats",
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, NOT_FIRST_STAGE_ERROR, msg="not first in $lookup sub-pipeline")


@pytest.mark.aggregate
def test_collStats_not_first_in_unionwith_sub_pipeline(collection):
    """Test that $collStats not first in $unionWith sub-pipeline produces an error."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$collStats": {"count": {}}},
                {
                    "$unionWith": {
                        "coll": collection.name,
                        "pipeline": [
                            {"$match": {}},
                            {"$collStats": {"count": {}}},
                        ],
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, NOT_FIRST_STAGE_ERROR, msg="not first in $unionWith sub-pipeline")


# Property [Stage Position Requirement - Facet Error]: $collStats inside a
# $facet sub-pipeline produces FACET_PIPELINE_INVALID_STAGE_ERROR.
@pytest.mark.aggregate
def test_collStats_in_facet_error(collection):
    """Test that $collStats inside $facet produces an error."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$facet": {"stats": [{"$collStats": {}}]}}],
            "cursor": {},
        },
    )
    assertFailureCode(result, FACET_PIPELINE_INVALID_STAGE_ERROR, msg="$collStats in $facet")


# Property [Stage Argument Type Validation - Extra Keys]: extra keys in the
# stage document produce PIPELINE_STAGE_EXTRA_FIELD_ERROR.
@pytest.mark.aggregate
def test_collStats_stage_extra_keys_error(collection):
    """Test that extra keys in the stage document produce an error."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [SON([("$collStats", {}), ("$match", {})])],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        40323,
        msg="extra keys in stage",
    )
