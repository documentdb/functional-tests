"""Tests for setFeatureCompatibilityVersion writeConcern field acceptance.

Validates that writeConcern accepts valid object values, null-as-omitted,
empty-doc, omission, and various numeric types for wtimeout.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.setFeatureCompatibilityVersion_common import get_fcv

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# Property [writeConcern Accepted]: setFeatureCompatibilityVersion accepts
# valid writeConcern values and various numeric types for wtimeout.
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
    CommandTestCase(
        "wtimeout_double",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "CURRENT_FCV",
            "confirm": True,
            "writeConcern": {"wtimeout": 5000.0},
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept wtimeout as double",
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
        msg="setFeatureCompatibilityVersion should accept wtimeout as Decimal128",
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
    cmd["setFeatureCompatibilityVersion"] = get_fcv(collection)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
