"""Tests for setFeatureCompatibilityVersion confirm field semantics (error cases).

Validates that omitting confirm or setting confirm:false prevents FCV changes.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import FCV_CONFIRM_REQUIRED_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Confirm Required]: version change without confirm (omitted or false) is rejected.
CONFIRM_REQUIRED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "downgrade_without_confirm",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV"},
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should reject downgrade without confirm field",
    ),
    CommandTestCase(
        "confirm_false_rejects_change",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": False,
        },
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should reject version change with confirm:false",
    ),
]

# Property [Upgrade Without Confirm]: upgrade without confirm is rejected.
UPGRADE_NO_CONFIRM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upgrade_without_confirm",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "ORIGINAL_FCV"},
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should reject upgrade without confirm",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFIRM_REQUIRED_TESTS))
def test_setFeatureCompatibilityVersion_confirm_required(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects change without valid confirm."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = get_fcv(collection)
    other = "8.0" if original != "8.0" else "8.2"
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = other
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(UPGRADE_NO_CONFIRM_TESTS))
def test_setFeatureCompatibilityVersion_upgrade_without_confirm(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects upgrade when confirm is omitted."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = get_fcv(collection)
    other = "8.0" if original != "8.0" else "8.2"
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": other, "confirm": True})
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = original
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": original, "confirm": True})
