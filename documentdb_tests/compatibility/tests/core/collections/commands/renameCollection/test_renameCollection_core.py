"""Tests for renameCollection core rename behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    ILLEGAL_OPERATION_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    TargetDatabase,
)

# Property [Self-Rename Rejection]: renaming a collection to itself
# (same source and target namespace) produces an illegal operation
# error.
RENAME_SELF_RENAME_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "self_rename_same_namespace",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": ctx.namespace,
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Renaming a collection to itself should be rejected",
    ),
]

# Property [Core Rename - Cross Database]: renaming a collection to a
# different database succeeds when the target database already exists.
RENAME_CROSS_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cross_db_basic",
        docs=[{"_id": 1, "x": "a"}, {"_id": 2, "x": "b"}],
        target_collection=TargetDatabase(suffix="cross_rename"),
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}_target.{ctx.collection}_renamed",
        },
        expected={"ok": 1.0},
        msg="Cross-db rename should succeed",
    ),
]

# Property [Core Rename - Auto-Create Target Database]: when the target
# database does not exist, it is auto-created upon successful rename.
RENAME_AUTO_CREATE_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "auto_create_target_db",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}_newdb.{ctx.collection}_renamed",
        },
        expected={"ok": 1.0},
        msg="Rename to non-existent target database should succeed",
    ),
]

# Property [Source Not Found]: renaming a collection that does not
# exist produces a namespace-not-found error.
RENAME_SOURCE_NOT_FOUND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "source_not_found",
        docs=None,
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Renaming a non-existent source collection should fail",
    ),
]

# Property [Unknown Top-Level Fields]: unrecognized fields at the
# command level produce an unrecognized-field error.
RENAME_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_top_level_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown top-level field should be rejected",
    ),
    CommandTestCase(
        "unknown_top_level_field_with_valid_options",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "dropTarget": False,
            "unknownField": "x",
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown field alongside valid options should be rejected",
    ),
]

RENAME_CORE_TESTS: list[CommandTestCase] = (
    RENAME_SELF_RENAME_REJECTION_TESTS
    + RENAME_CROSS_DB_TESTS
    + RENAME_AUTO_CREATE_DB_TESTS
    + RENAME_SOURCE_NOT_FOUND_TESTS
    + RENAME_UNKNOWN_FIELD_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_CORE_TESTS))
def test_renameCollection_core(database_client, collection, register_db_cleanup, test):
    """Test renameCollection core rename behavior."""
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
