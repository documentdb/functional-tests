"""Tests for aggregate command collection-agnostic mode."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_NAMESPACE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import ExistingDatabase

# Property [Collection-Agnostic Mode]: collection-agnostic pipelines
# execute successfully and produce the expected response shape.
AGGREGATE_AGNOSTIC_MODE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "agnostic_documents",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "cursor": {},
        },
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor": {"ns": Eq(f"{ctx.database}.$cmd.aggregate")},
        },
        msg="aggregate should accept $documents as collection-agnostic stage",
    ),
    CommandTestCase(
        "agnostic_list_local_sessions",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
        },
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor": {"ns": Eq(f"{ctx.database}.$cmd.aggregate")},
        },
        msg="aggregate should accept $listLocalSessions as collection-agnostic stage",
    ),
    CommandTestCase(
        "agnostic_with_optional_params",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "cursor": {},
            "allowDiskUse": True,
            "maxTimeMS": 5000,
        },
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor": {"ns": Eq(f"{ctx.database}.$cmd.aggregate")},
        },
        msg="aggregate should accept optional parameters in collection-agnostic mode",
    ),
]

# Property [Collection-Agnostic Rejection]: invalid uses of
# collection-agnostic mode are rejected.
AGGREGATE_AGNOSTIC_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "agnostic_empty_pipeline",
        command={"aggregate": 1, "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject empty pipeline in collection-agnostic mode",
    ),
    CommandTestCase(
        "documents_with_string_collection",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject $documents stage with a string collection name",
    ),
    CommandTestCase(
        "non_agnostic_stage_with_aggregate_1",
        command={"aggregate": 1, "pipeline": [{"$match": {"x": 1}}], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="aggregate should reject non-agnostic stage in collection-agnostic mode",
    ),
]

# Property [Collection-Agnostic Admin Stage]: $currentOp requires the admin
# database and produces the admin.$cmd.aggregate namespace.
AGGREGATE_AGNOSTIC_ADMIN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "agnostic_current_op",
        target_collection=ExistingDatabase(db_name="admin"),
        command={"aggregate": 1, "pipeline": [{"$currentOp": {}}], "cursor": {}},
        expected={"ok": Eq(1.0), "cursor": {"ns": Eq("admin.$cmd.aggregate")}},
        msg="aggregate should accept $currentOp as collection-agnostic stage on admin",
    ),
]

# Property [Collection-Agnostic Any Database]: collection-agnostic mode
# succeeds on non-existent databases.
AGGREGATE_AGNOSTIC_ANY_DATABASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "agnostic_nonexistent_database",
        target_collection=ExistingDatabase(db_name="nonexistent_db_agnostic_test"),
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"x": 1}]}],
            "cursor": {},
        },
        expected={
            "ok": Eq(1.0),
            "cursor": {"ns": Eq("nonexistent_db_agnostic_test.$cmd.aggregate")},
        },
        msg="aggregate should succeed in collection-agnostic mode on a non-existent database",
    ),
]

AGGREGATE_AGNOSTIC_TESTS = (
    AGGREGATE_AGNOSTIC_MODE_TESTS
    + AGGREGATE_AGNOSTIC_REJECTION_TESTS
    + AGGREGATE_AGNOSTIC_ADMIN_TESTS
    + AGGREGATE_AGNOSTIC_ANY_DATABASE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_AGNOSTIC_TESTS))
def test_aggregate_agnostic(database_client, collection, test):
    """Test aggregate collection-agnostic mode."""
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
