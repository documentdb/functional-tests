"""Tests for setFeatureCompatibilityVersion core behavior (success cases).

Validates idempotent set, downgrade/upgrade with confirm, and
getParameter readback after change.
"""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [Idempotent Set]: setting the current version succeeds and returns ok:1.
IDEMPOTENT_SET_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "idempotent_set_current_version",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "CURRENT_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed idempotently when re-setting"
        " current version",
    ),
]


# Property [Downgrade]: setFeatureCompatibilityVersion can downgrade with confirm:true.
DOWNGRADE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "downgrade_with_confirm",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when downgrading version with confirm",
    ),
]


# Property [Upgrade]: setFeatureCompatibilityVersion can upgrade back.
UPGRADE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upgrade_with_confirm",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "ORIGINAL_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when upgrading version with confirm",
    ),
]


# Property [GetParameter Reflects Change]: getParameter returns the new version after change.
GET_PARAMETER_AFTER_CHANGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "getParameter_reflects_change",
        command=lambda ctx: {"getParameter": 1, "featureCompatibilityVersion": 1},
        expected={"ok": 1.0},
        msg="getParameter should return the new version after setFeatureCompatibilityVersion",
    ),
]


@pytest.mark.parametrize("test", pytest_params(IDEMPOTENT_SET_TESTS))
def test_setFeatureCompatibilityVersion_idempotent_set(database_client, collection, test):
    """Test setFeatureCompatibilityVersion succeeds when re-setting the current version."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = get_fcv(collection)
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": fcv, "confirm": True})
    result = execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": fcv, "confirm": True}
    )
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(DOWNGRADE_TESTS))
def test_setFeatureCompatibilityVersion_downgrade(database_client, collection, test):
    """Test setFeatureCompatibilityVersion can downgrade with confirm:true."""
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
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": original, "confirm": True})


@pytest.mark.parametrize("test", pytest_params(UPGRADE_TESTS))
def test_setFeatureCompatibilityVersion_upgrade(database_client, collection, test):
    """Test setFeatureCompatibilityVersion can upgrade back to the original version."""
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


@pytest.mark.parametrize("test", pytest_params(GET_PARAMETER_AFTER_CHANGE_TESTS))
def test_setFeatureCompatibilityVersion_getParameter_reflects_change(
    database_client, collection, test
):
    """Test getParameter returns the new version after setFeatureCompatibilityVersion."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = get_fcv(collection)
    other = "8.0" if original != "8.0" else "8.2"
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": other, "confirm": True})
    result = execute_admin_command(collection, test.build_command(ctx))
    expected = {"ok": 1.0, "featureCompatibilityVersion": {"version": other}}
    assertSuccessPartial(result, expected, msg=test.msg)
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": original, "confirm": True})
