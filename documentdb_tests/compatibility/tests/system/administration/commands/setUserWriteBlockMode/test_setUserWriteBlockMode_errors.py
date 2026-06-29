"""Tests for setUserWriteBlockMode error cases.

Validates mismatched reason errors and idempotent behavior with same reason.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import ILLEGAL_OPERATION_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


def _force_disable_write_block(collection):
    """Force-disable write block regardless of current reason."""
    admin = collection.database.client.admin
    try:
        admin.command({"setUserWriteBlockMode": 1, "global": False})
        return
    except Exception:
        pass
    for reason in [
        "Unspecified",
        "ClusterToClusterMigrationInProgress",
        "DiskUseThresholdExceeded",
    ]:
        try:
            admin.command({"setUserWriteBlockMode": 1, "global": False, "reason": reason})
            return
        except Exception:
            continue


@pytest.fixture(autouse=True)
def _manage_write_block(collection):
    """Ensure write block is disabled before and after each test."""
    _force_disable_write_block(collection)
    yield
    _force_disable_write_block(collection)


# --- Mismatched reason errors ---


def test_setUserWriteBlockMode_enable_mismatched_reason_fails(collection):
    """Test re-enabling with different reason fails with IllegalOperation."""
    execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    result = execute_admin_command(
        collection,
        {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": "ClusterToClusterMigrationInProgress",
        },
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="Mismatched reason on enable should fail with IllegalOperation",
    )


def test_setUserWriteBlockMode_disable_mismatched_reason_fails(collection):
    """Test disabling with different reason than enabled fails with IllegalOperation."""
    execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    result = execute_admin_command(
        collection,
        {
            "setUserWriteBlockMode": 1,
            "global": False,
            "reason": "ClusterToClusterMigrationInProgress",
        },
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="Mismatched reason on disable should fail with IllegalOperation",
    )


# --- Idempotent with same reason ---


def test_setUserWriteBlockMode_same_reason_unspecified_idempotent(collection):
    """Test re-enabling with same reason 'Unspecified' succeeds (idempotent)."""
    execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="Same reason Unspecified re-enable should be idempotent"
    )


def test_setUserWriteBlockMode_same_reason_migration_idempotent(collection):
    """Test re-enabling with same reason 'ClusterToClusterMigrationInProgress' succeeds."""
    execute_admin_command(
        collection,
        {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": "ClusterToClusterMigrationInProgress",
        },
    )
    result = execute_admin_command(
        collection,
        {
            "setUserWriteBlockMode": 1,
            "global": True,
            "reason": "ClusterToClusterMigrationInProgress",
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="Same reason ClusterToClusterMigrationInProgress re-enable should be idempotent",
    )
