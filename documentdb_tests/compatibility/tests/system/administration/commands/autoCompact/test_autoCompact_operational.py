"""Tests for autoCompact operational constraints: admin scope and reconfigure conflict."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.system.administration.commands.autoCompact.utils.autoCompact_common import (  # noqa: E501
    ensure_autocompact_idle,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    ALREADY_INITIALIZED_ERROR,
    OBJECT_IS_BUSY_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_admin_with_retry_command,
    execute_command,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Admin-Scope Errors]: a fully valid autoCompact run against a
# non-admin database is rejected as out of scope.
AUTOCOMPACT_ADMIN_SCOPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "admin_scope_enable",
        command=lambda ctx: {"autoCompact": True},
        error_code=UNAUTHORIZED_ERROR,
        msg="autoCompact enable should be rejected when run against a non-admin database",
    ),
    CommandTestCase(
        "admin_scope_disable",
        command=lambda ctx: {"autoCompact": False},
        error_code=UNAUTHORIZED_ERROR,
        msg="autoCompact disable should be rejected when run against a non-admin database",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AUTOCOMPACT_ADMIN_SCOPE_TESTS))
def test_autoCompact_admin_scope(database_client, collection, test):
    """Test autoCompact admin-scope rejection against a non-admin database."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    # Run against the fixture's non-admin database so the admin-scope check can
    # fire. It happens at dispatch, independent of compaction state, so no
    # settling is needed here.
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Running-State Reconfigure Conflict]: reconfiguring an enabled
# autoCompact with a different config is rejected with a conflict error rather
# than silently overriding the running config.
@pytest.mark.no_parallel
def test_autoCompact_reconfigure_conflict(collection):
    """Test autoCompact rejects a differing reconfigure while enabled."""
    ensure_autocompact_idle(collection)

    # Establish a running config.
    execute_admin_with_retry_command(
        collection, {"autoCompact": True, "freeSpaceTargetMB": 30}, retry_code=OBJECT_IS_BUSY_ERROR
    )

    # A differing reconfigure is rejected while running; tolerate the transient
    # busy state while a prior compaction winds down.
    result = execute_admin_with_retry_command(
        collection, {"autoCompact": True, "freeSpaceTargetMB": 50}, retry_code=OBJECT_IS_BUSY_ERROR
    )

    assertResult(
        result,
        error_code=ALREADY_INITIALIZED_ERROR,
        msg="autoCompact should reject reconfiguring an enabled compaction with a different config",
        raw_res=True,
    )


# Property [Running-State Idempotent Reconfigure]: re-enabling an already
# enabled autoCompact with an identical config is accepted as a no-op rather
# than rejected, confirming the reconfigure conflict is driven by the config
# difference and not the already-running state.
@pytest.mark.no_parallel
def test_autoCompact_reconfigure_idempotent(collection):
    """Test autoCompact accepts re-enabling an enabled compaction with an identical config."""
    ensure_autocompact_idle(collection)

    # Establish a running config.
    execute_admin_with_retry_command(
        collection, {"autoCompact": True, "freeSpaceTargetMB": 30}, retry_code=OBJECT_IS_BUSY_ERROR
    )

    # Re-enabling an identical config is a no-op; tolerate the transient busy
    # state while a prior compaction winds down.
    result = execute_admin_with_retry_command(
        collection, {"autoCompact": True, "freeSpaceTargetMB": 30}, retry_code=OBJECT_IS_BUSY_ERROR
    )

    assertResult(
        result,
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept re-enabling an enabled compaction with an identical config",
        raw_res=True,
    )
