"""Tests for connectionStatus showPrivileges parameter.

Verifies the truthy/falsy/omit behavior of the showPrivileges field.
Truthy values (true, int 1, double 1.0, long 1, decimal128 1) should cause
authenticatedUserPrivileges to appear as an array. Falsy values (false,
int 0, double 0.0, long 0, decimal128 0, null) and omitting the field
entirely should exclude authenticatedUserPrivileges from the response.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import IsType, NotExists

pytestmark = pytest.mark.admin


TRUTHY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "true",
        command={"connectionStatus": 1, "showPrivileges": True},
        checks={"authInfo": {"authenticatedUserPrivileges": IsType("array")}},
        msg="true should show privileges",
    ),
    DiagnosticTestCase(
        "int_1",
        command={"connectionStatus": 1, "showPrivileges": 1},
        checks={"authInfo": {"authenticatedUserPrivileges": IsType("array")}},
        msg="int 1 (truthy) should show privileges",
    ),
    DiagnosticTestCase(
        "double_1",
        command={"connectionStatus": 1, "showPrivileges": 1.0},
        checks={"authInfo": {"authenticatedUserPrivileges": IsType("array")}},
        msg="double 1.0 (truthy) should show",
    ),
    DiagnosticTestCase(
        "long_1",
        command={"connectionStatus": 1, "showPrivileges": Int64(1)},
        checks={"authInfo": {"authenticatedUserPrivileges": IsType("array")}},
        msg="long 1 (truthy) should show",
    ),
    DiagnosticTestCase(
        "decimal128_1",
        command={"connectionStatus": 1, "showPrivileges": Decimal128("1")},
        checks={"authInfo": {"authenticatedUserPrivileges": IsType("array")}},
        msg="decimal128 1 should show",
    ),
    DiagnosticTestCase(
        "int_neg1",
        command={"connectionStatus": 1, "showPrivileges": -1},
        checks={"authInfo": {"authenticatedUserPrivileges": IsType("array")}},
        msg="int -1 (truthy) should show privileges",
    ),
    DiagnosticTestCase(
        "double_neg1",
        command={"connectionStatus": 1, "showPrivileges": -1.0},
        checks={"authInfo": {"authenticatedUserPrivileges": IsType("array")}},
        msg="double -1.0 (truthy) should show",
    ),
]

FALSY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "false",
        command={"connectionStatus": 1, "showPrivileges": False},
        checks={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        msg="false should hide privileges",
    ),
    DiagnosticTestCase(
        "int_0",
        command={"connectionStatus": 1, "showPrivileges": 0},
        checks={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        msg="int 0 (falsy) should hide privileges",
    ),
    DiagnosticTestCase(
        "double_0",
        command={"connectionStatus": 1, "showPrivileges": 0.0},
        checks={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        msg="double 0.0 (falsy) should hide",
    ),
    DiagnosticTestCase(
        "long_0",
        command={"connectionStatus": 1, "showPrivileges": Int64(0)},
        checks={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        msg="long 0 (falsy) should hide",
    ),
    DiagnosticTestCase(
        "decimal128_0",
        command={"connectionStatus": 1, "showPrivileges": Decimal128("0")},
        checks={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        msg="decimal128 0 should hide",
    ),
    DiagnosticTestCase(
        "null",
        command={"connectionStatus": 1, "showPrivileges": None},
        checks={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        msg="null (falsy) should hide privileges",
    ),
]

OMIT_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="omit_showPrivileges",
        command={"connectionStatus": 1},
        checks={"authInfo": {"authenticatedUserPrivileges": NotExists()}},
        msg="Omitting showPrivileges should not return privileges",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TRUTHY_TESTS))
def test_connectionStatus_show_privileges_truthy(collection, test):
    """Verify a truthy showPrivileges value includes authenticatedUserPrivileges as an array."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


@pytest.mark.parametrize("test", pytest_params(FALSY_TESTS))
def test_connectionStatus_show_privileges_falsy(collection, test):
    """Verify a falsy showPrivileges value excludes authenticatedUserPrivileges."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


@pytest.mark.parametrize("test", pytest_params(OMIT_TESTS))
def test_connectionStatus_omit_showPrivileges(collection, test):
    """Verify omitting showPrivileges excludes authenticatedUserPrivileges (same as false)."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
