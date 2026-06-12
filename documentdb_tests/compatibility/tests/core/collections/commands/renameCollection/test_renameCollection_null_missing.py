"""Tests for renameCollection null and missing field behavior."""

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
    MISSING_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Behavior (Success)]: when optional fields
# (writeConcern, comment) are null or omitted, or writeConcern is an
# empty object, the command succeeds.
RENAME_NULL_MISSING_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_ok_write_concern_empty_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "writeConcern": {},
        },
        expected={"ok": 1.0},
        msg="writeConcern={} (empty object) should be treated as default",
    ),
    CommandTestCase(
        "null_ok_comment",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "comment": None,
        },
        expected={"ok": 1.0},
        msg="comment=null should be accepted without error",
    ),
    CommandTestCase(
        "null_ok_write_concern_omitted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "comment": "test",
        },
        expected={"ok": 1.0},
        msg="Omitting writeConcern should use the default",
    ),
    CommandTestCase(
        "null_ok_comment_omitted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "writeConcern": {"w": 1},
        },
        expected={"ok": 1.0},
        msg="Omitting comment should succeed",
    ),
    CommandTestCase(
        "null_ok_collection_uuid_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "collectionUUID": None,
        },
        expected={"ok": 1.0},
        msg="collectionUUID=null should skip UUID validation",
    ),
    CommandTestCase(
        "null_ok_write_concern_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_renamed",
            "writeConcern": None,
        },
        expected={"ok": 1.0},
        msg="writeConcern=null should succeed",
    ),
]

# Property [Null and Missing Behavior (Errors)]: when required fields
# (renameCollection, to) are null or omitted, the server returns a
# missing-field error.
RENAME_NULL_MISSING_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_err_rename_collection",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": None,
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=MISSING_FIELD_ERROR,
        msg="renameCollection=null should be treated as missing",
    ),
    CommandTestCase(
        "null_err_to",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": None,
        },
        error_code=MISSING_FIELD_ERROR,
        msg="to=null should be treated as missing",
    ),
    CommandTestCase(
        "null_err_to_omitted",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
        },
        error_code=MISSING_FIELD_ERROR,
        msg="to omitted should be treated as missing",
    ),
]

RENAME_NULL_MISSING_TESTS: list[CommandTestCase] = (
    RENAME_NULL_MISSING_SUCCESS_TESTS + RENAME_NULL_MISSING_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_NULL_MISSING_TESTS))
def test_renameCollection_null_missing(database_client, collection, register_db_cleanup, test):
    """Test renameCollection null and missing field behavior."""
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
