"""Tests for whatsmyuri command response structure.

Validates presence, types, and values of response fields returned
by whatsmyuri. The response contains a 'you' field with the client's
connection URI (ip:port) and the standard 'ok' field.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType, NonEmptyStr

pytestmark = pytest.mark.admin


# Property [Response Structure]: whatsmyuri returns ok and a non-empty you field.
PROPERTY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="ok_is_1",
        checks={"ok": Eq(1.0)},
        msg="whatsmyuri should return ok equal to 1.0",
    ),
    DiagnosticTestCase(
        id="ok_is_double",
        checks={"ok": IsType("double")},
        msg="whatsmyuri should return ok as a double",
    ),
    DiagnosticTestCase(
        id="you_exists",
        checks={"you": Exists()},
        msg="whatsmyuri should return a you field",
    ),
    DiagnosticTestCase(
        id="you_is_string",
        checks={"you": IsType("string")},
        msg="whatsmyuri should return you as a string",
    ),
    DiagnosticTestCase(
        id="you_is_non_empty",
        checks={"you": NonEmptyStr()},
        msg="whatsmyuri should return a non-empty you field containing the client URI",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROPERTY_TESTS))
def test_whatsmyuri_response_properties(collection, test):
    """Test whatsmyuri response structure."""
    result = execute_admin_command(collection, {"whatsmyuri": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Property [URI Format]: the you field contains an ip:port pair with a colon separator.
def test_whatsmyuri_you_contains_colon(collection):
    """Test whatsmyuri you field contains ip:port separator."""
    result = execute_admin_command(collection, {"whatsmyuri": 1})
    you = result["you"]
    if ":" not in you:
        raise AssertionError(f"whatsmyuri you field should contain ':' (ip:port), got {you!r}")


def test_whatsmyuri_you_port_is_numeric(collection):
    """Test whatsmyuri you field has a numeric port."""
    result = execute_admin_command(collection, {"whatsmyuri": 1})
    you = result["you"]
    port = you.rsplit(":", 1)[-1]
    if not port.isdigit():
        raise AssertionError(
            f"whatsmyuri you field should have a numeric port after ':', got {you!r}"
        )
