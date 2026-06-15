"""Tests for renameCollection namespace length limits."""

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
    INVALID_NAMESPACE_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Namespace Length Limits (Success)]: a namespace of exactly
# 255 bytes and a database name of exactly 63 bytes are accepted;
# a 4-byte emoji at the 255-byte boundary is accepted.
RENAME_NAMESPACE_LENGTH_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "target_namespace_255_bytes",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{'a' * (255 - len(ctx.database.encode()) - 1)}",
        },
        expected={"ok": 1.0},
        msg="Target namespace of exactly 255 bytes should be accepted",
    ),
    CommandTestCase(
        "target_db_name_63_bytes",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{'b' * 63}.dest",
        },
        expected={"ok": 1.0},
        msg="Target database name of exactly 63 bytes should be accepted",
    ),
    CommandTestCase(
        "target_namespace_255_bytes_emoji",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            # pad + 4-byte emoji = total 255 bytes
            "to": f"{ctx.database}.{'a' * (255 - len(ctx.database.encode()) - 1 - 4)}\U0001f389",
        },
        expected={"ok": 1.0},
        msg="4-byte emoji at 255-byte namespace boundary should be accepted",
    ),
]

# Property [Namespace Length Limits (Errors)]: full namespace must be
# ≤ 255 bytes (256+ → illegal operation) and database name must be
# ≤ 63 bytes (64+ → invalid namespace); limits are byte-based.
RENAME_NAMESPACE_LENGTH_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "target_namespace_256_bytes",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{'a' * (256 - len(ctx.database.encode()) - 1)}",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Target namespace of 256 bytes should be rejected",
    ),
    CommandTestCase(
        "source_namespace_256_bytes",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": f"{ctx.database}.{'a' * (256 - len(ctx.database.encode()) - 1)}",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="Source namespace of 256 bytes should be rejected",
    ),
    CommandTestCase(
        "target_db_name_64_bytes",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{'b' * 64}.dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Target database name of 64 bytes should be rejected",
    ),
    CommandTestCase(
        "source_db_name_64_bytes",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": f"{'b' * 64}.src",
            "to": f"{ctx.database}.{ctx.collection}_dest",
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Source database name of 64 bytes should be rejected",
    ),
    CommandTestCase(
        "target_namespace_256_bytes_emoji",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            # pad + 4-byte emoji = total 256 bytes
            "to": f"{ctx.database}.{'a' * (256 - len(ctx.database.encode()) - 1 - 4)}\U0001f389",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="4-byte emoji pushing namespace to 256 bytes should be rejected",
    ),
]

RENAME_NAMESPACE_LENGTH_TESTS: list[CommandTestCase] = (
    RENAME_NAMESPACE_LENGTH_SUCCESS_TESTS + RENAME_NAMESPACE_LENGTH_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_NAMESPACE_LENGTH_TESTS))
def test_renameCollection_namespace_length(database_client, collection, register_db_cleanup, test):
    """Test renameCollection namespace length limits."""
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
