"""Wiring tests for validate command 'checkBSONConformance' parameter type coercion.

Confirms checkBSONConformance uses the same boolean coercion as other params.
The full BSON type matrix is in test_validate_bool_param_coercion.py.
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

# Property [Type Coercion Wiring]: checkBSONConformance delegates to shared boolean coercion.
WIRING_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        command={"checkBSONConformance": True},
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept bool true",
    ),
    DiagnosticTestCase(
        "int32_0",
        command={"checkBSONConformance": 0},
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "string",
        command={"checkBSONConformance": "true"},
        checks={"ok": Eq(1.0)},
        msg="checkBSONConformance should accept string (coerces to truthy)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WIRING_TESTS))
def test_validate_checkBSONConformance_accepted_types(collection, test):
    """Test that checkBSONConformance uses shared boolean coercion."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, **test.command},
    )
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
