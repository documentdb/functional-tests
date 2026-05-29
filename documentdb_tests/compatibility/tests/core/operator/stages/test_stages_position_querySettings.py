"""Tests for $querySettings pipeline position and composition."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    INVALID_NAMESPACE_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ExistingDatabase

# Property [Subsequent Read/Transform Stages]: $querySettings composes
# with a subsequent read or transform stage without error.
QUERYSETTINGS_SUBSEQUENT_READ_TRANSFORM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "subsequent_match",
        command={
            "aggregate": 1,
            "pipeline": [{"$querySettings": {}}, {"$match": {"queryShapeHash": "nonexistent"}}],
            "cursor": {},
        },
        expected=[],
        msg="$querySettings should compose with a subsequent $match stage",
    ),
    CommandTestCase(
        "subsequent_project",
        command={
            "aggregate": 1,
            "pipeline": [{"$querySettings": {}}, {"$project": {"queryShapeHash": 1}}],
            "cursor": {},
        },
        expected=[],
        msg="$querySettings should compose with a subsequent $project stage",
    ),
    CommandTestCase(
        "subsequent_sort",
        command={
            "aggregate": 1,
            "pipeline": [{"$querySettings": {}}, {"$sort": {"queryShapeHash": 1}}],
            "cursor": {},
        },
        expected=[],
        msg="$querySettings should compose with a subsequent $sort stage",
    ),
    CommandTestCase(
        "subsequent_group",
        command={
            "aggregate": 1,
            "pipeline": [{"$querySettings": {}}, {"$group": {"_id": "$queryShapeHash"}}],
            "cursor": {},
        },
        expected=[],
        msg="$querySettings should compose with a subsequent $group stage",
    ),
]

# Property [Subsequent Write Stages]: $out and $merge can follow
# $querySettings, writing the output stream to a user database without
# error.
QUERYSETTINGS_SUBSEQUENT_WRITE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "subsequent_out_to_user_db",
        command=lambda ctx: {
            "aggregate": 1,
            "pipeline": [{"$querySettings": {}}, {"$out": {"db": ctx.database, "coll": "qs_out"}}],
            "cursor": {},
        },
        expected=[],
        msg=(
            "$querySettings should compose with a subsequent $out stage"
            " targeting a regular user database"
        ),
    ),
    CommandTestCase(
        "subsequent_merge_to_user_db",
        command=lambda ctx: {
            "aggregate": 1,
            "pipeline": [
                {"$querySettings": {}},
                {"$merge": {"into": {"db": ctx.database, "coll": "qs_merge"}}},
            ],
            "cursor": {},
        },
        expected=[],
        msg=(
            "$querySettings should compose with a subsequent $merge stage"
            " targeting a regular user database"
        ),
    ),
]

# Property [Pipeline Position Errors - Not First]: $querySettings appearing
# after another stage in a pipeline is rejected with NOT_FIRST_STAGE_ERROR.
# This includes a second $querySettings stage following a first one.
QUERYSETTINGS_NOT_FIRST_STAGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "position_error_after_documents",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"a": 1}]}, {"$querySettings": {}}],
            "cursor": {},
        },
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$querySettings should be rejected when not the first stage in a pipeline",
    ),
    CommandTestCase(
        "position_error_two_querysettings",
        command={
            "aggregate": 1,
            "pipeline": [{"$querySettings": {}}, {"$querySettings": {}}],
            "cursor": {},
        },
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$querySettings should reject a second $querySettings stage in the same pipeline",
    ),
]

# Property [Pipeline Position Errors - In $facet]: $querySettings inside a
# $facet sub-pipeline is rejected with FACET_PIPELINE_INVALID_STAGE_ERROR.
QUERYSETTINGS_FACET_STAGE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "position_error_inside_facet",
        command={
            "aggregate": 1,
            "pipeline": [{"$facet": {"sub": [{"$querySettings": {}}]}}],
            "cursor": {},
        },
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$querySettings should be rejected inside a $facet sub-pipeline",
    ),
]

# Property [Pipeline Position]: $querySettings is valid as the first stage
# in a pipeline against any database, including non-existent databases,
# returning zero documents without error.
QUERYSETTINGS_PIPELINE_POSITION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "position_first_stage_test_db",
        docs=[{"_id": 1}],
        command={"aggregate": 1, "pipeline": [{"$querySettings": {}}], "cursor": {}},
        expected=[],
        msg="$querySettings should succeed as the first stage on a regular user database",
    ),
    CommandTestCase(
        "position_first_stage_local",
        target_collection=ExistingDatabase(db_name="local"),
        command={"aggregate": 1, "pipeline": [{"$querySettings": {}}], "cursor": {}},
        expected=[],
        msg="$querySettings should succeed as the first stage on local",
    ),
    CommandTestCase(
        "position_first_stage_config",
        target_collection=ExistingDatabase(db_name="config"),
        command={"aggregate": 1, "pipeline": [{"$querySettings": {}}], "cursor": {}},
        expected=[],
        msg="$querySettings should succeed as the first stage on config",
    ),
    CommandTestCase(
        "position_first_stage_nonexistent_db",
        docs=None,
        command={"aggregate": 1, "pipeline": [{"$querySettings": {}}], "cursor": {}},
        expected=[],
        msg="$querySettings should succeed as the first stage on a non-existent database",
    ),
]

# Property [Collection-Level Aggregation]: $querySettings is rejected with
# INVALID_NAMESPACE_ERROR in a collection-level aggregation context,
# including direct collection-level aggregation and $unionWith / $lookup
# sub-pipelines.
QUERYSETTINGS_COLLECTION_LEVEL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_level_direct",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$querySettings": {}}],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$querySettings should be rejected when run as a collection-level aggregation",
    ),
    CommandTestCase(
        "collection_level_inside_union_with",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$unionWith": {"coll": ctx.collection, "pipeline": [{"$querySettings": {}}]}}
            ],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$querySettings should be rejected inside a $unionWith sub-pipeline",
    ),
    CommandTestCase(
        "collection_level_inside_lookup",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "pipeline": [{"$querySettings": {}}],
                        "as": "r",
                    }
                }
            ],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$querySettings should be rejected inside a $lookup sub-pipeline",
    ),
]

QUERYSETTINGS_POSITION_TESTS = (
    QUERYSETTINGS_SUBSEQUENT_READ_TRANSFORM_TESTS
    + QUERYSETTINGS_SUBSEQUENT_WRITE_TESTS
    + QUERYSETTINGS_NOT_FIRST_STAGE_ERROR_TESTS
    + QUERYSETTINGS_FACET_STAGE_ERROR_TESTS
    + QUERYSETTINGS_PIPELINE_POSITION_TESTS
    + QUERYSETTINGS_COLLECTION_LEVEL_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(QUERYSETTINGS_POSITION_TESTS))
def test_querySettings_position(
    database_client: Database, collection: Collection, test: CommandTestCase
):
    """Test $querySettings pipeline position and composition with other stages."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
