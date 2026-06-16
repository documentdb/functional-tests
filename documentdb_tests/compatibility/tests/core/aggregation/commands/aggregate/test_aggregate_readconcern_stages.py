"""Tests for aggregate command readConcern stage restrictions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    NOT_A_REPLICA_SET_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import ExistingDatabase

# Property [readConcern Stage Restrictions Acceptance]: stages with
# readConcern restrictions accept their permitted levels.
# Note: $currentOp is tested in the admin section below because it requires
# the admin database.
AGGREGATE_READCONCERN_STAGE_RESTRICTIONS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_stage_collstats_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$collStats": {"count": {}}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'local' with $collStats",
    ),
    CommandTestCase(
        "rc_stage_collstats_available",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$collStats": {"count": {}}}],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'available' with $collStats",
    ),
    CommandTestCase(
        "rc_stage_collstats_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$collStats": {"count": {}}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'majority' with $collStats",
    ),
    CommandTestCase(
        "rc_stage_indexstats_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$indexStats": {}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'local' with $indexStats",
    ),
    CommandTestCase(
        "rc_stage_indexstats_available",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$indexStats": {}}],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'available' with $indexStats",
    ),
    CommandTestCase(
        "rc_stage_indexstats_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$indexStats": {}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'majority' with $indexStats",
    ),
    CommandTestCase(
        "rc_stage_listlocalsessions_local",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'local' with $listLocalSessions",
    ),
    CommandTestCase(
        "rc_stage_plancachestats_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'local' with $planCacheStats",
    ),
]

# Property [readConcern Stage Restrictions Rejection]: stages with
# readConcern restrictions reject levels outside their permitted set.
AGGREGATE_READCONCERN_STAGE_RESTRICTIONS_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_stage_out_linearizable",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": "out_coll"}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'linearizable' with $out",
    ),
    CommandTestCase(
        "rc_stage_merge_linearizable",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": "merge_coll"}}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'linearizable' with $merge",
    ),
    CommandTestCase(
        "rc_stage_listlocalsessions_available",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'available' with $listLocalSessions",
    ),
    CommandTestCase(
        "rc_stage_listlocalsessions_majority",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'majority' with $listLocalSessions",
    ),
    CommandTestCase(
        "rc_stage_plancachestats_available",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'available' with $planCacheStats",
    ),
    CommandTestCase(
        "rc_stage_plancachestats_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'majority' with $planCacheStats",
    ),
    # Stage restriction takes precedence over standalone rejection.
    CommandTestCase(
        "rc_stage_listlocalsessions_linearizable",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'linearizable' with $listLocalSessions",
    ),
    CommandTestCase(
        "rc_stage_listlocalsessions_snapshot",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
            "readConcern": {"level": "snapshot"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'snapshot' with $listLocalSessions",
    ),
    CommandTestCase(
        "rc_stage_plancachestats_linearizable",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'linearizable' with $planCacheStats",
    ),
    CommandTestCase(
        "rc_stage_plancachestats_snapshot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
            "cursor": {},
            "readConcern": {"level": "snapshot"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'snapshot' with $planCacheStats",
    ),
    # linearizable and snapshot are rejected on standalone when no stage
    # restriction takes precedence.
    CommandTestCase(
        "rc_standalone_linearizable",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
        error_code=NOT_A_REPLICA_SET_ERROR,
        msg="aggregate should reject readConcern 'linearizable' on standalone",
    ),
    CommandTestCase(
        "rc_standalone_snapshot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "snapshot"},
        },
        error_code=NOT_A_REPLICA_SET_ERROR,
        msg="aggregate should reject readConcern 'snapshot' on standalone",
    ),
]

# Property [readConcern Stage Restrictions Acceptance Admin]: $currentOp
# accepts only readConcern level "local" (requires admin database).
AGGREGATE_READCONCERN_STAGE_RESTRICTIONS_ADMIN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_stage_currentop_local",
        target_collection=ExistingDatabase(db_name="admin"),
        command={
            "aggregate": 1,
            "pipeline": [{"$currentOp": {}}],
            "cursor": {},
            "readConcern": {"level": "local"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept readConcern 'local' with $currentOp",
    ),
]

# Property [readConcern Stage Restrictions Rejection Admin]: $currentOp with
# levels other than local is rejected (requires admin database).
AGGREGATE_READCONCERN_STAGE_RESTRICTIONS_REJECTION_ADMIN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_stage_currentop_available",
        target_collection=ExistingDatabase(db_name="admin"),
        command={
            "aggregate": 1,
            "pipeline": [{"$currentOp": {}}],
            "cursor": {},
            "readConcern": {"level": "available"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'available' with $currentOp",
    ),
    CommandTestCase(
        "rc_stage_currentop_majority",
        target_collection=ExistingDatabase(db_name="admin"),
        command={
            "aggregate": 1,
            "pipeline": [{"$currentOp": {}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'majority' with $currentOp",
    ),
    CommandTestCase(
        "rc_stage_currentop_linearizable",
        target_collection=ExistingDatabase(db_name="admin"),
        command={
            "aggregate": 1,
            "pipeline": [{"$currentOp": {}}],
            "cursor": {},
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'linearizable' with $currentOp",
    ),
    CommandTestCase(
        "rc_stage_currentop_snapshot",
        target_collection=ExistingDatabase(db_name="admin"),
        command={
            "aggregate": 1,
            "pipeline": [{"$currentOp": {}}],
            "cursor": {},
            "readConcern": {"level": "snapshot"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="aggregate should reject readConcern 'snapshot' with $currentOp",
    ),
]

AGGREGATE_READCONCERN_STAGES_TESTS = (
    AGGREGATE_READCONCERN_STAGE_RESTRICTIONS_ACCEPTANCE_TESTS
    + AGGREGATE_READCONCERN_STAGE_RESTRICTIONS_REJECTION_TESTS
    + AGGREGATE_READCONCERN_STAGE_RESTRICTIONS_ADMIN_TESTS
    + AGGREGATE_READCONCERN_STAGE_RESTRICTIONS_REJECTION_ADMIN_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_READCONCERN_STAGES_TESTS))
def test_aggregate_readconcern_stages(database_client, collection, test):
    """Test aggregate readConcern stage restrictions."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
