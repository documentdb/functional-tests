"""Tests for ping command response structure.

Validates the response fields and their types.
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


RESPONSE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="ok_field_value",
        checks={"ok": Eq(1.0)},
        msg="'ok' field should be 1.0",
    ),
    DiagnosticTestCase(
        id="ok_field_type",
        checks={"ok": IsType("double")},
        msg="'ok' field should be a double",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_TESTS))
def test_ping_response_properties(collection, test):
    """Verifies ping response fields have expected types and values."""
    result = execute_admin_command(collection, {"ping": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
