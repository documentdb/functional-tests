"""Tests for setFeatureCompatibilityVersion writeConcern field validation.

Validates writeConcern type validation, null-as-omitted behavior,
empty-doc acceptance, and wtimeout coercion.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
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


# Property [writeConcern Accepted]: setFeatureCompatibilityVersion accepts
# valid writeConcern values.
WRITE_CONCERN_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "object",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"wtimeout": 5000},
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept writeConcern as object",
    ),
    CommandTestCase(
        "empty_object",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {},
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept writeConcern as empty object",
    ),
    CommandTestCase(
        "null_as_omitted",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": None,
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should treat writeConcern=null as omitted",
    ),
    CommandTestCase(
        "omitted",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should succeed when writeConcern is omitted",
    ),
]


# Property [writeConcern Rejected]: setFeatureCompatibilityVersion rejects
# non-object writeConcern types.
WRITE_CONCERN_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": "majority",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as string",
    ),
    CommandTestCase(
        "int",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": 1,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as int",
    ),
    CommandTestCase(
        "bool",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": True,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as bool",
    ),
    CommandTestCase(
        "array",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": [{"w": 1}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as array",
    ),
    CommandTestCase(
        "long",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": Int64(1),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as long",
    ),
    CommandTestCase(
        "double",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": 1.0,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as double",
    ),
    CommandTestCase(
        "decimal128",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": Decimal128("1"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="setFeatureCompatibilityVersion should reject writeConcern as Decimal128",
    ),
]


# Property [wtimeout Coercion]: setFeatureCompatibilityVersion accepts
# various numeric types for wtimeout.
WTIMEOUT_COERCION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_double",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"wtimeout": 5000.0},
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as whole-number double",
    ),
    CommandTestCase(
        "wtimeout_long",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"wtimeout": Int64(5000)},
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as Int64",
    ),
    CommandTestCase(
        "wtimeout_decimal_whole",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"wtimeout": Decimal128("5000")},
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as whole-number Decimal128",
    ),
    CommandTestCase(
        "wtimeout_fractional_double",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"wtimeout": 5000.5},
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as fractional double",
    ),
    CommandTestCase(
        "wtimeout_negative",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"wtimeout": -1},
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as negative value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_ACCEPTED_TESTS))
def test_setFeatureCompatibilityVersion_writeConcern_accepted(database_client, collection, test):
    """Test setFeatureCompatibilityVersion accepts valid writeConcern values."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = _get_fcv(collection)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_REJECTED_TESTS))
def test_setFeatureCompatibilityVersion_writeConcern_rejected(database_client, collection, test):
    """Test setFeatureCompatibilityVersion rejects non-object writeConcern types."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = _get_fcv(collection)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(WTIMEOUT_COERCION_TESTS))
def test_setFeatureCompatibilityVersion_wtimeout_coercion(database_client, collection, test):
    """Test setFeatureCompatibilityVersion accepts various numeric types for wtimeout."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cmd["setFeatureCompatibilityVersion"] = _get_fcv(collection)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
