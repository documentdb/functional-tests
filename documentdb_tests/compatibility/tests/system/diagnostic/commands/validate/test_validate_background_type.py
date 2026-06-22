"""Tests for validate command 'background' parameter type coercion.

Validates that the background parameter accepts all BSON types via coercion.
Note: background: true is not supported on standalone mode, so truthy values
are tested with assertFailureCode for the standalone error.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

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


@pytest.mark.parametrize("test", pytest_params(FALSY_TYPE_TESTS))
def test_validate_background_falsy_types(collection, test):
    """Test that validate accepts falsy types for the background parameter."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, **test.command},
    )
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [Truthy Standalone Error]: validate rejects truthy background values on standalone mode.
TRUTHY_TYPE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "bool_true",
        command={"background": True},
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: true not supported on standalone",
    ),
    DiagnosticTestCase(
        "int32_1",
        command={"background": 1},
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: int 1 (truthy) not supported on standalone",
    ),
    DiagnosticTestCase(
        "string",
        command={"background": "true"},
        error_code=COMMAND_NOT_SUPPORTED_ERROR,
        msg="background: string (truthy) not supported on standalone",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TRUTHY_TYPE_TESTS))
def test_validate_background_truthy_standalone_error(collection, test):
    """Test that background with truthy values errors on standalone mode."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"validate": collection.name, **test.command},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)
