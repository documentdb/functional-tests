"""Tests for profile command slowms parameter.

Validates slowms value persistence, boundary values, and null no-op behavior.
All tests in this file verify success cases only.
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
from documentdb_tests.framework.test_constants import INT32_MAX, INT32_MIN

pytestmark = [pytest.mark.no_parallel]

# Property [slowms Persistence]: setting slowms persists the value for
# subsequent reads.
SLOWMS_PERSISTENCE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "persist_200",
        setup=[{"profile": 0, "slowms": 200}],
        command={"profile": -1},
        checks={"slowms": Eq(200)},
        msg="slowms should persist value 200",
    ),
    DiagnosticTestCase(
        "persist_0",
        setup=[{"profile": 0, "slowms": 0}],
        command={"profile": -1},
        checks={"slowms": Eq(0)},
        msg="slowms should persist value 0",
    ),
    DiagnosticTestCase(
        "persist_negative_value",
        setup=[{"profile": 0, "slowms": -1}],
        command={"profile": -1},
        checks={"slowms": Eq(-1)},
        msg="slowms should persist negative value -1",
    ),
]

# Property [slowms Boundary Values]: slowms accepts the full int32 range
# including negative values.
SLOWMS_BOUNDARY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "boundary_int32_max",
        setup=[{"profile": 0, "slowms": INT32_MAX}],
        command={"profile": -1},
        checks={"slowms": Eq(INT32_MAX)},
        msg="slowms should accept INT32_MAX",
    ),
    DiagnosticTestCase(
        "boundary_int32_min",
        setup=[{"profile": 0, "slowms": INT32_MIN}],
        command={"profile": -1},
        checks={"slowms": Eq(INT32_MIN)},
        msg="slowms should accept INT32_MIN",
    ),
    DiagnosticTestCase(
        "boundary_neg100",
        setup=[{"profile": 0, "slowms": -100}],
        command={"profile": -1},
        checks={"slowms": Eq(-100)},
        msg="slowms should accept -100",
    ),
]

# Property [slowms Null No-Op]: setting slowms to null does not change
# the current value.
SLOWMS_NULL_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "null_noop",
        setup=[
            {"profile": 0, "slowms": 500},
            {"profile": 0, "slowms": None},
        ],
        command={"profile": -1},
        checks={"slowms": Eq(500)},
        msg="slowms should remain 500 after setting null",
    ),
]

SLOWMS_TESTS = SLOWMS_PERSISTENCE_TESTS + SLOWMS_BOUNDARY_TESTS + SLOWMS_NULL_TESTS


@pytest.mark.parametrize("test", pytest_params(SLOWMS_TESTS))
def test_profile_slowms(collection, test):
    """Test profile slowms parameter behavior."""
    for cmd in test.setup:
        execute_command(collection, cmd)
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
    execute_command(collection, {"profile": 0, "slowms": 100})
