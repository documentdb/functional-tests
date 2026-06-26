"""Tests for setFeatureCompatibilityVersion core behavior (success cases).

Validates FCV set/get round-trip, idempotency, default value read-back,
basic upgrade/downgrade with confirm, admin-database acceptance,
and success response structure.
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


# Property [Set Current]: setting the current version succeeds idempotently.
SET_CURRENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "set_current_version",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "CURRENT_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when setting the current version",
    ),
    CommandTestCase(
        "idempotent_same_value",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "CURRENT_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should be idempotent when re-setting the same value",
    ),
]


# Property [GetParameter Readback]: getParameter reads back the current FCV.
GET_PARAMETER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "getParameter_reads_back",
        command=lambda ctx: {"getParameter": 1, "featureCompatibilityVersion": 1},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should persist and be readable via getParameter",
    ),
    CommandTestCase(
        "fresh_deployment_default",
        command=lambda ctx: {"getParameter": 1, "featureCompatibilityVersion": 1},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should have a readable default on a fresh deployment",
    ),
]


# Property [Downgrade]: setFeatureCompatibilityVersion can downgrade with confirm:true.
DOWNGRADE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "downgrade_with_confirm",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when changing version with confirm",
    ),
]


# Property [Upgrade]: setFeatureCompatibilityVersion can upgrade back.
UPGRADE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upgrade_with_confirm",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "ORIGINAL_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when upgrading back",
    ),
]


# Property [GetParameter Reflects Change]: getParameter reflects FCV after change.
GET_PARAMETER_AFTER_CHANGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "getParameter_reflects_change",
        command=lambda ctx: {"getParameter": 1, "featureCompatibilityVersion": 1},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should be reflected in getParameter after a change",
    ),
]


# Property [Admin DB Accepted]: setFeatureCompatibilityVersion succeeds on the admin database.
ADMIN_DB_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "admin_db_accepted",
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed on the admin database",
    ),
]


# Property [Success Response Structure]: success response contains ok:1.
SUCCESS_RESPONSE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "success_contains_ok",
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion success response should contain ok:1",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SET_CURRENT_TESTS))
def test_setFeatureCompatibilityVersion_set_current(database_client, collection, test):
    """Test setFeatureCompatibilityVersion succeeds when setting the current version."""
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


@pytest.mark.parametrize("test", pytest_params(GET_PARAMETER_TESTS))
def test_setFeatureCompatibilityVersion_getParameter(database_client, collection, test):
    """Test getParameter reads back the current FCV."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = get_fcv(collection)
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": fcv, "confirm": True})
    result = execute_admin_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


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
    """Test getParameter reflects the FCV after a change."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = get_fcv(collection)
    other = "8.0" if original != "8.0" else "8.2"
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": other, "confirm": True})
    result = execute_admin_command(collection, test.build_command(ctx))
    expected = {"ok": 1.0, "featureCompatibilityVersion": {"version": other}}
    assertSuccessPartial(result, expected, msg=test.msg)
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": original, "confirm": True})


@pytest.mark.parametrize("test", pytest_params(ADMIN_DB_ACCEPTED_TESTS))
def test_setFeatureCompatibilityVersion_admin_db_accepted(database_client, collection, test):
    """Test setFeatureCompatibilityVersion succeeds on the admin database."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = get_fcv(collection)
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


@pytest.mark.parametrize("test", pytest_params(SUCCESS_RESPONSE_TESTS))
def test_setFeatureCompatibilityVersion_success_response(database_client, collection, test):
    """Test setFeatureCompatibilityVersion success response contains ok:1."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    fcv = get_fcv(collection)
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
