"""Wiring tests for validate 'metadata' and 'background' parameter type coercion.

Confirms metadata uses the same boolean coercion as other params (wiring only).
The full BSON type matrix is in test_validate_bool_param_coercion.py.
Also tests that the background parameter accepts falsy BSON types.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Type Coercion Wiring]: metadata delegates to shared boolean coercion.
METADATA_WIRING_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        command={"metadata": True},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept bool true",
    ),
    DiagnosticTestCase(
        "int32_0",
        command={"metadata": 0},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "string",
        command={"metadata": "true"},
        checks={"ok": Eq(1.0)},
        msg="metadata should accept string (coerces to truthy)",
    ),
]


# Property [Falsy Type Acceptance]: validate accepts falsy BSON types for the background parameter.
FALSY_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_false",
        command={"background": False},
        checks={"ok": Eq(1.0)},
        msg="background should accept bool false",
    ),
    DiagnosticTestCase(
        "int32_0",
        command={"background": 0},
        checks={"ok": Eq(1.0)},
        msg="background should accept int32 0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "double_0",
        command={"background": 0.0},
        checks={"ok": Eq(1.0)},
        msg="background should accept double 0.0 (coerces to false)",
    ),
    DiagnosticTestCase(
        "int64_0",
        command={"background": Int64(0)},
        checks={"ok": Eq(1.0)},
        msg="background should accept Int64(0) (coerces to false)",
    ),
    DiagnosticTestCase(
        "decimal128_0",
        command={"background": Decimal128("0")},
        checks={"ok": Eq(1.0)},
        msg="background should accept Decimal128('0') (coerces to false)",
    ),
    DiagnosticTestCase(
        "null",
        command={"background": None},
        checks={"ok": Eq(1.0)},
        msg="background should accept null (treated as omitted/false)",
    ),
]


METADATA_AND_BACKGROUND_TESTS = METADATA_WIRING_TESTS + FALSY_TYPE_TESTS


@pytest.mark.parametrize("test", pytest_params(METADATA_AND_BACKGROUND_TESTS))
def test_validate_metadata_and_background_types(collection, test):
    """Test type coercion for metadata and background parameters."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, **test.command},
    )
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
