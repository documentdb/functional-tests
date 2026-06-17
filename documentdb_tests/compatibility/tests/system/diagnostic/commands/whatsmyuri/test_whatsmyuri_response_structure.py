"""Tests for whatsmyuri command response structure.

Validates presence, types, and values of response fields returned
by whatsmyuri. The response contains a 'you' field with the client's
connection URI (ip:port) and the standard 'ok' field.
"""

import re

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
_COLON_PATTERN = re.compile(r":")
_NUMERIC_PORT_PATTERN = re.compile(r":\d+$")


def test_whatsmyuri_you_contains_colon(collection):
    """Test whatsmyuri you field contains ip:port separator."""
    result = execute_admin_command(collection, {"whatsmyuri": 1})
    assertProperties(
        result,
        {"you": _MatchesRegex(_COLON_PATTERN, "contain ':'")},
        msg="whatsmyuri should return a you field containing a colon separator",
        raw_res=True,
    )


def test_whatsmyuri_you_port_is_numeric(collection):
    """Test whatsmyuri you field has a numeric port."""
    result = execute_admin_command(collection, {"whatsmyuri": 1})
    assertProperties(
        result,
        {"you": _MatchesRegex(_NUMERIC_PORT_PATTERN, "have a numeric port after ':'")},
        msg="whatsmyuri should return a you field with a numeric port",
        raw_res=True,
    )


class _MatchesRegex:
    """Inline check: assert that a string field matches a regex pattern."""

    def __init__(self, pattern: re.Pattern, description: str) -> None:
        self._pattern = pattern
        self._description = description

    def check(self, value, path: str):  # noqa: ANN001
        if not isinstance(value, str):
            return f"expected '{path}' to be a string, got {type(value).__name__}"
        if not self._pattern.search(value):
            return f"expected '{path}' to {self._description}, got {value!r}"
        return None

    def __repr__(self) -> str:
        return f"_MatchesRegex({self._pattern.pattern!r})"
