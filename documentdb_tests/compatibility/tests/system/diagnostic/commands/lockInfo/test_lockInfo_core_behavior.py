"""Tests for lockInfo command core behavior.

Verifies that lockInfo succeeds on admin database, returns a lockInfo array,
and behaves correctly under successive calls.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (  # IsType used in CORE_BEHAVIOR_TESTS
    Eq,
    IsType,
)

pytestmark = pytest.mark.admin


CORE_BEHAVIOR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="returns_ok",
        command={"lockInfo": 1},
        checks={"ok": Eq(1.0)},
        msg="lockInfo should return ok:1",
    ),
    DiagnosticTestCase(
        id="returns_lockInfo_array",
        command={"lockInfo": 1},
        checks={"lockInfo": IsType("array")},
        msg="lockInfo field should be array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_BEHAVIOR_TESTS))
def test_lockInfo_core_behavior(collection, test):
    """Verifies lockInfo returns expected fields on the admin database."""
    result = execute_admin_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


def test_lockInfo_point_in_time_snapshot(collection):
    """Test lockInfo result is a point-in-time snapshot (successive calls succeed)."""
    execute_admin_command(collection, {"lockInfo": 1})
    result = execute_admin_command(collection, {"lockInfo": 1})
    assertProperties(result, {"ok": Eq(1.0)}, msg="Successive calls should succeed", raw_res=True)
