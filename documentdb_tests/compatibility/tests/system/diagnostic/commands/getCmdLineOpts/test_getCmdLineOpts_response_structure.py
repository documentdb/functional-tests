"""Tests for getCmdLineOpts command response structure.

Validates presence, types, and values of response fields.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType

pytestmark = pytest.mark.admin


PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="ok_is_1",
        checks={"ok": Eq(1.0)},
        msg="'ok' field should be 1.0",
    ),
    DiagnosticTestCase(
        id="argv_is_array",
        checks={"argv": IsType("array")},
        msg="'argv' field should be an array",
    ),
    DiagnosticTestCase(
        id="argv_first_is_string",
        checks={"argv.0": IsType("string")},
        msg="'argv' first element (binary path) should be a string",
    ),
    DiagnosticTestCase(
        id="parsed_is_object",
        checks={"parsed": IsType("object")},
        msg="'parsed' field should be a document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_getCmdLineOpts_response_properties(collection, test):
    """Verifies getCmdLineOpts response fields have expected types and values."""
    result = execute_admin_command(collection, {"getCmdLineOpts": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
