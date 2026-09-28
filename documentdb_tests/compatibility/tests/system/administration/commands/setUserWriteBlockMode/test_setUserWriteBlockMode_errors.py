"""Tests for setUserWriteBlockMode error cases.

Validates mismatched reason errors when changing the reason on an active block.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.administration.commands.setUserWriteBlockMode.utils.write_block_helpers import (  # noqa: E501
    force_disable_write_block,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import ILLEGAL_OPERATION_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]


@pytest.fixture(autouse=True)
def _manage_write_block(collection):
    """Ensure write block is disabled before and after each test."""
    force_disable_write_block(collection)
    yield
    force_disable_write_block(collection)


# Property [Mismatched Reason on Enable]: re-enabling with a different reason fails.
def test_setUserWriteBlockMode_enable_mismatched_reason_fails(collection):
    """Test setUserWriteBlockMode re-enable with different reason fails."""
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
        msg="setUserWriteBlockMode should reject mismatched reason on re-enable",
    )


# Property [Mismatched Reason on Disable]: disabling with a different reason than the active
# block fails.
def test_setUserWriteBlockMode_disable_mismatched_reason_fails(collection):
    """Test setUserWriteBlockMode disable with different reason fails."""
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
        msg="setUserWriteBlockMode should reject mismatched reason on disable",
    )


# Property [Mismatched Reason on Enable]: re-enabling with DiskUseThresholdExceeded when a
# different reason is active fails.
def test_setUserWriteBlockMode_enable_mismatched_reason_disk_threshold_fails(collection):
    """Test setUserWriteBlockMode re-enable with DiskUseThresholdExceeded over another reason."""
    execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "DiskUseThresholdExceeded"},
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="setUserWriteBlockMode should reject mismatched reason on re-enable",
    )


# Property [Mismatched Reason on Disable]: disabling with DiskUseThresholdExceeded when a
# different reason is active fails.
def test_setUserWriteBlockMode_disable_mismatched_reason_disk_threshold_fails(collection):
    """Test setUserWriteBlockMode disable with DiskUseThresholdExceeded over another reason."""
    execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": True, "reason": "Unspecified"},
    )
    result = execute_admin_command(
        collection,
        {"setUserWriteBlockMode": 1, "global": False, "reason": "DiskUseThresholdExceeded"},
    )
    assertFailureCode(
        result,
        ILLEGAL_OPERATION_ERROR,
        msg="setUserWriteBlockMode should reject mismatched reason on disable",
    )
