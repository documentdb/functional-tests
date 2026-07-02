"""Tests for lockInfo command response structure.

Verifies the top-level structure of the lockInfo response: ok field and
lockInfo array field. Also verifies the structure of individual lock entries
using an fsync lock to guarantee a non-empty snapshot.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


RESPONSE_STRUCTURE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "ok_field",
        checks={"ok": Eq(1.0)},
        msg="Response should contain ok: 1.0",
    ),
    DiagnosticTestCase(
        "lockInfo_is_array",
        checks={"lockInfo": IsType("array")},
        msg="lockInfo field should be an array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_lockInfo_response_structure(collection, test):
    """Verify lockInfo response contains expected fields with correct types."""
    result = execute_admin_command(collection, {"lockInfo": 1})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_lockInfo_entry_structure(collection):
    """Test a lock entry exposes resourceId (string), granted (array), and pending (array).

    Acquires a global fsync lock so the lock manager reports at least one entry,
    guaranteeing the assertion runs against a real lock entry rather than an
    empty snapshot. Must not run in parallel — fsyncLock is a global server lock.
    """
    execute_admin_command(collection, {"fsync": 1, "lock": True})
    try:
        result = execute_admin_command(collection, {"lockInfo": 1})
        entry = result["lockInfo"][0]
    finally:
        execute_admin_command(collection, {"fsyncUnlock": 1})
    assertProperties(
        entry,
        {
            "resourceId": IsType("string"),
            "granted": IsType("array"),
            "pending": IsType("array"),
        },
        msg="lock entry should expose resourceId (string), granted (array), pending (array)",
        raw_res=True,
    )
