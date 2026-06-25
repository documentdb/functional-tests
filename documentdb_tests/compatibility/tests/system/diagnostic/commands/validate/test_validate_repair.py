"""Wiring tests for validate command repair and fixMultikey options.

Confirms repair and fixMultikey use the same boolean coercion as other params
(wiring only). The full BSON type matrix is in test_validate_bool_param_coercion.py.
Also verifies repairMode values for different repair configurations.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = pytest.mark.requires(validate_repair=True)

# Property [Type Coercion Wiring]: repair delegates to shared boolean coercion.
REPAIR_WIRING_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "repair_bool_true",
        command={"repair": True},
        checks={"ok": Eq(1.0)},
        msg="repair should accept bool true",
    ),
    DiagnosticTestCase(
        "repair_int32_0",
        command={"repair": 0},
        checks={"ok": Eq(1.0)},
        msg="repair should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "repair_string",
        command={"repair": "true"},
        checks={"ok": Eq(1.0)},
        msg="repair should accept string (coerces to truthy)",
    ),
]

# Property [Type Coercion Wiring]: fixMultikey delegates to shared boolean coercion.
FIXMULTIKEY_WIRING_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "fixMultikey_bool_true",
        command={"fixMultikey": True},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept bool true",
    ),
    DiagnosticTestCase(
        "fixMultikey_int32_0",
        command={"fixMultikey": 0},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "fixMultikey_string",
        command={"fixMultikey": "true"},
        checks={"ok": Eq(1.0)},
        msg="fixMultikey should accept string (coerces to truthy)",
    ),
]

# Property [Repair Mode]: validate returns correct repairMode for different configurations.
REPAIR_MODE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "no_repair_mode_none",
        command={},
        checks={"ok": Eq(1.0), "repairMode": Eq("None"), "repaired": Eq(False)},
        msg="validate should return repairMode: 'None' with no repair options",
    ),
    DiagnosticTestCase(
        "repair_and_fixMultikey_mode_fix_errors",
        command={"repair": True, "fixMultikey": True},
        checks={"ok": Eq(1.0), "repairMode": Eq("FixErrors"), "repaired": Eq(False)},
        msg="validate with repair+fixMultikey should return repairMode: 'FixErrors'",
    ),
    DiagnosticTestCase(
        "fixMultikey_alone_mode_adjust",
        command={"fixMultikey": True},
        checks={"ok": Eq(1.0), "repairMode": Eq("AdjustMultikey"), "repaired": Eq(False)},
        msg="validate with fixMultikey alone should return repairMode: 'AdjustMultikey'",
    ),
    DiagnosticTestCase(
        "repair_alone_mode_fix_errors",
        command={"repair": True},
        checks={"ok": Eq(1.0), "repairMode": Eq("FixErrors"), "repaired": Eq(False)},
        msg="validate with repair alone should return repairMode: 'FixErrors'",
    ),
]


REPAIR_AND_FIXMULTIKEY_TESTS = REPAIR_WIRING_TESTS + FIXMULTIKEY_WIRING_TESTS + REPAIR_MODE_TESTS


@pytest.mark.parametrize("test", pytest_params(REPAIR_AND_FIXMULTIKEY_TESTS))
def test_validate_repair_and_fixMultikey(collection, test):
    """Test repair/fixMultikey type coercion and repairMode values."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, **test.command},
    )
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
