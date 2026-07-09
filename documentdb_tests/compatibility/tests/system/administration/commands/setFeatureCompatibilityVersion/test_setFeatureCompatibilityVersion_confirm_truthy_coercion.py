"""Tests for setFeatureCompatibilityVersion confirm field truthy coercion.

Validates that the confirm field accepts truthy numeric values
(int 1, double 1.0, Int64(1), Decimal128("1"), NaN, Infinity, -Infinity).
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
    CommandTestCase(
        "negative_infinity",
        command=lambda ctx: {
            "setFeatureCompatibilityVersion": "OTHER_FCV",
            "confirm": float("-inf"),
        },
        expected={"ok": 1.0},
        msg="setFeatureCompatibilityVersion should accept confirm=-Infinity as true",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFIRM_TRUTHY_TESTS))
def test_setFeatureCompatibilityVersion_confirm_truthy(database_client, collection, test):
    """Test setFeatureCompatibilityVersion accepts truthy confirm values."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    current = get_fcv(collection)
    other = "8.0" if current != "8.0" else "8.2"
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
    execute_admin_command(collection, {"setFeatureCompatibilityVersion": current, "confirm": True})
