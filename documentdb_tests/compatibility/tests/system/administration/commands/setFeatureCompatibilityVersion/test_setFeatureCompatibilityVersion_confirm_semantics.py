"""Tests for setFeatureCompatibilityVersion confirm field semantics.

Validates that the confirm field is required for version changes,
and that confirm:false or omitted confirm prevents FCV changes.
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

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def _get_fcv(collection):
    """Read the current FCV via getParameter."""
    result = execute_admin_command(
        collection, {"getParameter": 1, "featureCompatibilityVersion": 1}
    )
    if isinstance(result, Exception):
        return "8.2"
    fcv_data = result.get("featureCompatibilityVersion", {})
    if isinstance(fcv_data, dict):
        return fcv_data.get("version", "8.2")
    return str(fcv_data)


def _set_fcv(collection, version):
    """Set FCV with confirm:true."""
    return execute_admin_command(
        collection, {"setFeatureCompatibilityVersion": version, "confirm": True}
    )


def _get_other_fcv(current):
    """Get a different supported FCV than the current one."""
    return "8.0" if current != "8.0" else "8.2"


# Property [Confirm Required]: confirm:true is required for version changes.
CONFIRM_TRUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "confirm_true_allows_change",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should allow version change with confirm:true",
    ),
]

# Property [Confirm Omitted]: omitting confirm prevents version changes.
CONFIRM_OMITTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "confirm_omitted",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV"},
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should reject version change without confirm",
    ),
]

# Property [Confirm False]: confirm:false prevents version changes.
CONFIRM_FALSE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "confirm_false",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": False},
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

# Property [Upgrade With Confirm]: upgrade with confirm:true succeeds.
UPGRADE_WITH_CONFIRM_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "upgrade_with_confirm",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "ORIGINAL_FCV", "confirm": True},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed on upgrade with confirm:true",
    ),
]


def _resolve_fcv_placeholders(command_dict, **replacements):
    """Replace FCV placeholders in a command dict."""
    resolved = {}
    for k, v in command_dict.items():
        if isinstance(v, str) and v in replacements:
            resolved[k] = replacements[v]
        else:
            resolved[k] = v
    return resolved


@pytest.mark.parametrize("test", pytest_params(CONFIRM_TRUE_TESTS))
def test_setFeatureCompatibilityVersion_confirm_true_allows_change(
    database_client, collection, test
):
    """Test setFeatureCompatibilityVersion succeeds with confirm:true."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = _get_fcv(collection)
    other = _get_other_fcv(original)
    cmd = _resolve_fcv_placeholders(test.build_command(ctx), OTHER_FCV=other)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
    _set_fcv(collection, original)


@pytest.mark.parametrize("test", pytest_params(CONFIRM_OMITTED_TESTS))
def test_setFeatureCompatibilityVersion_confirm_omitted_fails(database_client, collection, test):
    """Test setFeatureCompatibilityVersion fails when confirm is omitted."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = _get_fcv(collection)
    other = _get_other_fcv(original)
    cmd = _resolve_fcv_placeholders(test.build_command(ctx), OTHER_FCV=other)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(CONFIRM_FALSE_TESTS))
def test_setFeatureCompatibilityVersion_confirm_false_fails(database_client, collection, test):
    """Test setFeatureCompatibilityVersion fails with confirm:false."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = _get_fcv(collection)
    other = _get_other_fcv(original)
    cmd = _resolve_fcv_placeholders(test.build_command(ctx), OTHER_FCV=other)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(UPGRADE_NO_CONFIRM_TESTS))
def test_setFeatureCompatibilityVersion_upgrade_without_confirm_fails(
    database_client, collection, test
):
    """Test setFeatureCompatibilityVersion rejects upgrade without confirm."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = _get_fcv(collection)
    other = _get_other_fcv(original)
    _set_fcv(collection, other)
    cmd = _resolve_fcv_placeholders(test.build_command(ctx), ORIGINAL_FCV=original)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
    _set_fcv(collection, original)


@pytest.mark.parametrize("test", pytest_params(UPGRADE_WITH_CONFIRM_TESTS))
def test_setFeatureCompatibilityVersion_upgrade_with_confirm_succeeds(
    database_client, collection, test
):
    """Test setFeatureCompatibilityVersion succeeds on upgrade with confirm:true."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    original = _get_fcv(collection)
    other = _get_other_fcv(original)
    _set_fcv(collection, other)
    cmd = _resolve_fcv_placeholders(test.build_command(ctx), ORIGINAL_FCV=original)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
