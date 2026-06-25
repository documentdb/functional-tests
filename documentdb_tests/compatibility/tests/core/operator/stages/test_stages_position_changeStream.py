"""Tests for $changeStream pipeline position constraints and stage composition."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    ILLEGAL_OPERATION_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import ExistingDatabase

# Property [Following Stage Allow-List]: $changeStream opens as the first stage
# and the pipeline opens successfully when followed by any stage permitted in
# its allow-list.
CHANGESTREAM_FOLLOWING_STAGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "following_match",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$match": {"operationType": "insert"}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $match",
    ),
    CommandTestCase(
        "following_project",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$project": {"_id": 1}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $project",
    ),
    CommandTestCase(
        "following_add_fields",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$addFields": {"x": 1}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $addFields",
    ),
    CommandTestCase(
        "following_set",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$set": {"x": 1}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $set",
    ),
    CommandTestCase(
        "following_replace_root",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$replaceRoot": {"newRoot": {"a": 1}}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $replaceRoot",
    ),
    CommandTestCase(
        "following_replace_with",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$replaceWith": {"a": 1}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $replaceWith",
    ),
    CommandTestCase(
        "following_redact",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$redact": "$$DESCEND"}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $redact",
    ),
    CommandTestCase(
        "following_unset",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$unset": "x"}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $unset",
    ),
    CommandTestCase(
        "following_fill",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$fill": {"output": {"x": {"value": 0}}}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $fill",
    ),
    CommandTestCase(
        "following_change_stream_split_large_event",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$changeStreamSplitLargeEvent": {}}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open when followed by $changeStreamSplitLargeEvent",
    ),
]

# Property [Disallowed Following Stage Rejection]: a stage outside the
# $changeStream allow-list placed after $changeStream is rejected, including
# stages that desugar to a disallowed system stage (e.g. $count and
# $sortByCount desugar to $group; $densify and $setWindowFields desugar to
# $sort; $fill with a sortBy desugars to $sort).
CHANGESTREAM_DISALLOWED_FOLLOWING_STAGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "disallowed_group",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$group": {"_id": "$operationType"}}],
            "cursor": {},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="$changeStream should reject a following $group stage",
    ),
    CommandTestCase(
        "disallowed_sort",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$sort": {"_id": 1}}],
            "cursor": {},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="$changeStream should reject a following $sort stage",
    ),
    CommandTestCase(
        "disallowed_count",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$changeStream": {}}, {"$count": "n"}],
            "cursor": {},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="$changeStream should reject a following $count stage",
    ),
    CommandTestCase(
        "disallowed_bucket",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$changeStream": {}},
                {"$bucket": {"groupBy": "$x", "boundaries": [0, 1, 2], "default": "other"}},
            ],
            "cursor": {},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="$changeStream should reject a following $bucket stage",
    ),
    CommandTestCase(
        "disallowed_densify",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$changeStream": {}},
                {"$densify": {"field": "x", "range": {"step": 1, "bounds": "full"}}},
            ],
            "cursor": {},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="$changeStream should reject a following $densify stage",
    ),
    CommandTestCase(
        "disallowed_set_window_fields",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$changeStream": {}},
                {"$setWindowFields": {"sortBy": {"x": 1}, "output": {"n": {"$sum": 1}}}},
            ],
            "cursor": {},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="$changeStream should reject a following $setWindowFields stage",
    ),
    CommandTestCase(
        "disallowed_fill_with_sort_by",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$changeStream": {}},
                {"$fill": {"sortBy": {"x": 1}, "output": {"y": {"method": "linear"}}}},
            ],
            "cursor": {},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="$changeStream should reject a following $fill stage that desugars to $sort",
    ),
]

# Property [Stage Position Rejection]: $changeStream placed anywhere other than
# the first stage of the pipeline is rejected with a not-first-stage error in
# every namespace scope.
#
# The collection-less (database/cluster) forms use $documents as the leading
# stage because it is valid in a collection-less pipeline; a collection-
# requiring stage such as $match would fail with an invalid-namespace error
# before $changeStream's position check runs, masking it.
CHANGESTREAM_STAGE_POSITION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "not_first_collection",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {}}, {"$changeStream": {}}],
            "cursor": {},
        },
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$changeStream should reject a non-first stage position in a collection pipeline",
    ),
    CommandTestCase(
        "not_first_database",
        docs=[{"_id": 1}],
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}, {"$changeStream": {}}],
            "cursor": {},
        },
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$changeStream should reject a non-first stage position in a database-scoped pipeline",
    ),
    CommandTestCase(
        "not_first_cluster",
        target_collection=ExistingDatabase(db_name="admin"),
        docs=None,
        command={
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{"x": 1}]},
                {"$changeStream": {"allChangesForCluster": True}},
            ],
            "cursor": {},
        },
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$changeStream should reject a non-first stage position in a cluster-scoped pipeline",
    ),
]

CHANGESTREAM_POSITION_TESTS = (
    CHANGESTREAM_FOLLOWING_STAGE_TESTS
    + CHANGESTREAM_DISALLOWED_FOLLOWING_STAGE_TESTS
    + CHANGESTREAM_STAGE_POSITION_ERROR_TESTS
)


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(CHANGESTREAM_POSITION_TESTS))
def test_changeStream_position(
    database_client: Database, collection: Collection, test: CommandTestCase
):
    """Test $changeStream pipeline position constraints and stage composition."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(target, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
