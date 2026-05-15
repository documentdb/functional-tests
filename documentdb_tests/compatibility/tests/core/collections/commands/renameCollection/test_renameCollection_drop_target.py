"""Tests for renameCollection dropTarget behavior."""

import uuid

import pytest
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    COLLECTION_UUID_MISMATCH_ERROR,
    INVALID_OPTIONS_ERROR,
    INVALID_UUID_ERROR,
    NAMESPACE_EXISTS_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    SiblingCollection,
    TargetDatabase,
)

# Property [dropTarget Boolean Success]: when dropTarget is true or
# false and no target collection exists, the rename succeeds.
RENAME_DROP_TARGET_BOOL_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "drop_target_true_no_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": True,
        },
        expected={"ok": 1.0},
        msg="dropTarget=true with no target should succeed",
    ),
    CommandTestCase(
        "drop_target_false_no_target",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": False,
        },
        expected={"ok": 1.0},
        msg="dropTarget=false with no target should succeed",
    ),
]

# Property [dropTarget Behavior - Existing Target]: when dropTarget is
# true and the target collection exists, the target is dropped and the
# rename succeeds.
RENAME_DROP_TARGET_EXISTING_TARGET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "drop_target_true_existing_target",
        docs=[{"_id": 1, "src": True}],
        siblings=[SiblingCollection(suffix="_target", docs=[{"_id": 99, "tgt": True}])],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": True,
        },
        expected={"ok": 1.0},
        msg="dropTarget=true should succeed when target exists",
    ),
]

# Property [dropTarget Behavior (UUID - Success)]: dropTarget accepts
# Binary subtype 4 (UUID), and when the UUID matches the target
# collection's UUID, the target is dropped and the rename succeeds.
RENAME_DROP_TARGET_UUID_MATCH_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "drop_target_uuid_match",
        docs=[{"_id": 1, "src": True}],
        siblings=[SiblingCollection(suffix="_target", docs=[{"_id": 99, "tgt": True}])],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": ctx.uuids[f"{ctx.collection}_target"],
        },
        expected={"ok": 1.0},
        msg="dropTarget with matching UUID should succeed",
    ),
]

# Property [dropTarget Behavior (UUID - Errors)]: when dropTarget is a
# UUID that does not match the target collection, the target does not
# exist, the source does not exist, or the rename is cross-database,
# the command fails; invalid Binary values produce InvalidUUID.
RENAME_DROP_TARGET_UUID_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "uuid_mismatch_target_exists",
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_target", docs=[{"_id": 99}])],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": Binary(uuid.uuid4().bytes, 4),
        },
        error_code=COLLECTION_UUID_MISMATCH_ERROR,
        msg="UUID not matching existing target's UUID should fail",
    ),
    CommandTestCase(
        "uuid_mismatch_target_not_exists",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_nonexistent",
            "dropTarget": Binary(uuid.uuid4().bytes, 4),
        },
        error_code=COLLECTION_UUID_MISMATCH_ERROR,
        msg="UUID check occurs even when target does not exist",
    ),
    CommandTestCase(
        "uuid_mismatch_source_not_exists",
        docs=None,
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": Binary(uuid.uuid4().bytes, 4),
        },
        error_code=COLLECTION_UUID_MISMATCH_ERROR,
        msg="UUID check occurs even when source does not exist",
    ),
    CommandTestCase(
        "uuid_cross_db_prohibited",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}_other.{ctx.collection}_target",
            "dropTarget": Binary(uuid.uuid4().bytes, 4),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="UUID dropTarget is prohibited for cross-database renames",
    ),
    CommandTestCase(
        "binary_wrong_subtype",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": Binary(b"\x00" * 16, 3),
        },
        error_code=INVALID_UUID_ERROR,
        msg="Binary subtype 3 (not UUID subtype 4) should produce InvalidUUID",
    ),
    CommandTestCase(
        "binary_wrong_length",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": Binary(b"\x00" * 8, 4),
        },
        error_code=INVALID_UUID_ERROR,
        msg="Binary subtype 4 with wrong length should produce InvalidUUID",
    ),
    CommandTestCase(
        "binary_default_subtype",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": Binary(b"data"),
        },
        error_code=INVALID_UUID_ERROR,
        msg="Binary default subtype 0 should produce InvalidUUID",
    ),
]

# Property [dropTarget Behavior (Boolean - Errors)]: when dropTarget is
# false (or omitted) and the target exists, or when dropTarget is true
# but the target is a view or timeseries collection, the command fails
# with a namespace-exists error.
RENAME_DROP_TARGET_BOOLEAN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "drop_target_false_target_exists",
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_target", docs=[{"_id": 99}])],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": False,
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="dropTarget=false with existing target should fail",
    ),
    CommandTestCase(
        "drop_target_omitted_target_exists",
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_target", docs=[{"_id": 99}])],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="dropTarget omitted with existing target should fail",
    ),
    CommandTestCase(
        "drop_target_true_target_is_view",
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_target", view_on_source=True)],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": True,
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="dropTarget=true with target as view should fail",
    ),
    CommandTestCase(
        "drop_target_true_target_is_timeseries",
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_target", timeseries_field="ts")],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_target",
            "dropTarget": True,
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="dropTarget=true with target as timeseries should fail",
    ),
]

# Property [dropTarget Behavior - Cross Database]: when dropTarget is
# true and the rename is cross-database, the target is dropped and the
# rename succeeds.
RENAME_DROP_TARGET_CROSS_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "drop_target_true_cross_db",
        docs=[{"_id": 1, "src": True}],
        target_collection=TargetDatabase(suffix="drop_cross"),
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}_dest.{ctx.collection}_target",
            "dropTarget": True,
        },
        expected={"ok": 1.0},
        msg="dropTarget=true cross-db rename should succeed",
    ),
]

RENAME_DROP_TARGET_TESTS: list[CommandTestCase] = (
    RENAME_DROP_TARGET_BOOL_SUCCESS_TESTS
    + RENAME_DROP_TARGET_EXISTING_TARGET_TESTS
    + RENAME_DROP_TARGET_UUID_MATCH_TESTS
    + RENAME_DROP_TARGET_UUID_ERROR_TESTS
    + RENAME_DROP_TARGET_BOOLEAN_ERROR_TESTS
    + RENAME_DROP_TARGET_CROSS_DB_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_DROP_TARGET_TESTS))
def test_renameCollection_drop_target(database_client, collection, register_db_cleanup, test):
    """Test renameCollection dropTarget behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cross_db_cleanup_ns(cmd, ctx, register_db_cleanup)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
