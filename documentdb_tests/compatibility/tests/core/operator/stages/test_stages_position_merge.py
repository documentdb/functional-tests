"""Tests for $merge pipeline position and nesting restrictions."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    INVALID_OPTIONS_ERROR,
    LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
    OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
    OUT_NOT_LAST_STAGE_ERROR,
    UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
)
from documentdb_tests.framework.executor import execute_command


# Property [Pipeline Position]: $merge must be the last stage in a pipeline.
@pytest.mark.aggregate
def test_stages_position_merge_not_last_stage(collection):
    """Test $merge not as the last stage produces a pipeline position error."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$merge": {"into": "target"}}, {"$match": {"_id": 1}}],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        OUT_NOT_LAST_STAGE_ERROR,
        msg="$merge not as the last stage should produce a pipeline position error",
    )


# Property [Nested Pipeline - $lookup]: $merge is not allowed inside a
# $lookup sub-pipeline.
@pytest.mark.aggregate
def test_stages_position_merge_inside_lookup(collection):
    """Test $merge inside a $lookup nested pipeline is rejected."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": "other",
                        "pipeline": [{"$merge": {"into": "target"}}],
                        "as": "r",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        LOOKUP_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$merge inside a $lookup nested pipeline should be rejected",
    )


# Property [Nested Pipeline - $facet]: $merge is not allowed inside a $facet
# sub-pipeline.
@pytest.mark.aggregate
def test_stages_position_merge_inside_facet(collection):
    """Test $merge inside a $facet nested pipeline is rejected."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$facet": {"branch": [{"$merge": {"into": "target"}}]}}],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$merge inside a $facet nested pipeline should be rejected",
    )


# Property [Nested Pipeline - $unionWith]: $merge is not allowed inside a
# $unionWith sub-pipeline.
@pytest.mark.aggregate
def test_stages_position_merge_inside_union_with(collection):
    """Test $merge inside a $unionWith nested pipeline is rejected."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$unionWith": {"coll": "other", "pipeline": [{"$merge": {"into": "target"}}]}}
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        UNION_WITH_SUB_PIPELINE_NOT_ALLOWED_ERROR,
        msg="$merge inside a $unionWith nested pipeline should be rejected",
    )


# Property [View Definition]: $merge in a view definition is rejected.
@pytest.mark.aggregate
def test_stages_position_merge_in_view_definition(collection):
    """Test $merge in a view definition is rejected."""
    db = collection.database
    collection.insert_one({"_id": 1})
    view_name = f"{collection.name}_bad_view"
    db.drop_collection(view_name)

    result = execute_command(
        collection,
        {
            "create": view_name,
            "viewOn": collection.name,
            "pipeline": [{"$merge": {"into": "target"}}],
        },
    )
    assertFailureCode(
        result,
        OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$merge in a view definition should produce an invalid view pipeline error",
    )


# Property [Target Restriction - View]: $merge targeting a view is rejected.
@pytest.mark.aggregate
def test_stages_position_merge_target_view(collection):
    """Test $merge targeting a view is rejected."""
    db = collection.database
    collection.insert_one({"_id": 1})
    view_name = f"{collection.name}_view_target"
    db.drop_collection(view_name)
    db.command({"create": view_name, "viewOn": collection.name, "pipeline": []})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$merge": {"into": view_name}}],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$merge targeting a view should be rejected",
    )


# Property [Target Restriction - Time Series]: $merge targeting a time series
# collection is rejected.
@pytest.mark.aggregate
def test_stages_position_merge_target_timeseries(collection):
    """Test $merge targeting a time series collection is rejected."""
    db = collection.database
    collection.insert_one({"_id": 1})
    ts_name = f"{collection.name}_ts_target"
    db.drop_collection(ts_name)
    db.command({"create": ts_name, "timeseries": {"timeField": "ts"}})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$merge": {"into": ts_name}}],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$merge targeting a time series collection should be rejected",
    )


# Property [Read Concern]: linearizable read concern with $merge produces an
# invalid options error.
@pytest.mark.aggregate
def test_stages_position_merge_linearizable_read_concern(collection):
    """Test $merge rejects linearizable read concern."""
    collection.insert_one({"_id": 1})
    target = f"{collection.name}_linearizable"

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$merge": {"into": target}}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
    )
    assertFailureCode(
        result,
        INVALID_OPTIONS_ERROR,
        msg="$merge should reject linearizable read concern",
    )
