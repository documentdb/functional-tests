"""Tests for setFeatureCompatibilityVersion confirm field type coercion.

Validates how the confirm field handles various BSON types beyond bool,
recording coercion behavior (accepted-as-true vs rejected/treated-as-false).
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import FCV_CONFIRM_REQUIRED_ERROR, TYPE_MISMATCH_ERROR
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


# Property [Truthy Coercion]: confirm field accepts truthy numeric values.
CONFIRM_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int_1",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": 1},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=1 (int) as true",
    ),
    CommandTestCase(
        "double_1",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": 1.0},
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=1.0 (double) as true",
    ),
    CommandTestCase(
        "long_1",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": Int64(1),
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=Int64(1) as true",
    ),
    CommandTestCase(
        "decimal_1",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": Decimal128("1"),
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=Decimal128('1') as true",
    ),
    CommandTestCase(
        "nan",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": float("nan"),
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=NaN as true",
    ),
    CommandTestCase(
        "infinity",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": float("inf"),
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=Infinity as true",
    ),
]


# Property [Falsy Coercion]: confirm field treats falsy values as false,
# requiring confirm to be truthy.
CONFIRM_FALSY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int_0",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": 0},
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=0 as false",
    ),
    CommandTestCase(
        "double_0",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": 0.0},
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=0.0 as false",
    ),
    CommandTestCase(
        "long_0",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": Int64(0),
        },
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=Int64(0) as false",
    ),
    CommandTestCase(
        "decimal_0",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": Decimal128("0"),
        },
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=Decimal128('0') as false",
    ),
    CommandTestCase(
        "null",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": None},
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=null as not-true",
    ),
    CommandTestCase(
        "negative_zero",
        command=lambda ctx: {"setFeatureCompatibilityVersion": "OTHER_FCV", "confirm": -0.0},
        error_code=FCV_CONFIRM_REQUIRED_ERROR,
        msg="setFeatureCompatibilityVersion should treat confirm=-0.0 as false",
    ),
]


# Property [Type Rejected]: confirm field rejects non-numeric, non-bool types.
CONFIRM_TYPE_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": "true",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as string type",
    ),
    CommandTestCase(
        "object",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": {"a": 1},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as object type",
    ),
    CommandTestCase(
        "array",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": [True],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject confirm as array type",
    ),
]


def _resolve_fcv_placeholders(command_dict, current_fcv, other_fcv):
    """Replace FCV placeholders in a command dict."""
    resolved = {}
    for k, v in command_dict.items():
        if v == "CURRENT_FCV":
            resolved[k] = current_fcv
        elif v == "OTHER_FCV":
            resolved[k] = other_fcv
        else:
            resolved[k] = v
    return resolved


@pytest.mark.parametrize("test", pytest_params(CONFIRM_TRUTHY_TESTS))
def test_setFeatureCompatibilityVersion_confirm_truthy(database_client, collection, test):
    """Test setFeatureCompatibilityVersion accepts truthy confirm values."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    current = _get_fcv(collection)
    other = _get_other_fcv(current)
    cmd = _resolve_fcv_placeholders(test.build_command(ctx), current, other)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
    _set_fcv(collection, current)


@pytest.mark.parametrize("test", pytest_params(CONFIRM_FALSY_TESTS))
def test_setFeatureCompatibilityVersion_confirm_falsy(database_client, collection, test):
    """Test setFeatureCompatibilityVersion treats falsy confirm values as false."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    current = _get_fcv(collection)
    other = _get_other_fcv(current)
    cmd = _resolve_fcv_placeholders(test.build_command(ctx), current, other)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(CONFIRM_TYPE_REJECTED_TESTS))
def test_setFeatureCompatibilityVersion_confirm_type_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects non-numeric, non-bool confirm types."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    current = _get_fcv(collection)
    other = _get_other_fcv(current)
    cmd = _resolve_fcv_placeholders(test.build_command(ctx), current, other)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
