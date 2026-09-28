"""Tests for profile command sampleRate parameter.

Validates sampleRate value persistence, boundary values, and null no-op behavior.
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

pytestmark = [pytest.mark.no_parallel]

# Property [sampleRate Persistence]: setting sampleRate persists the value
# for subsequent reads.
SAMPLERATE_PERSISTENCE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "persist_0_5",
        setup=[{"profile": 0, "sampleRate": 0.5}],
        command={"profile": -1},
        checks={"sampleRate": Eq(0.5)},
        msg="sampleRate should persist value 0.5",
    ),
    DiagnosticTestCase(
        "persist_boundary_zero",
        setup=[{"profile": 0, "sampleRate": 0.0}],
        command={"profile": -1},
        checks={"sampleRate": Eq(0.0)},
        msg="sampleRate should persist value 0.0",
    ),
    DiagnosticTestCase(
        "persist_1_0",
        setup=[{"profile": 0, "sampleRate": 1.0}],
        command={"profile": -1},
        checks={"sampleRate": Eq(1.0)},
        msg="sampleRate should persist value 1.0",
    ),
]

# Property [sampleRate Boundary Acceptance]: sampleRate accepts boundary
# values within [0, 1] using int and double types.
SAMPLERATE_BOUNDARY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "boundary_int_0",
        setup=[{"profile": 0, "sampleRate": 0}],
        command={"profile": -1},
        checks={"sampleRate": Eq(0.0)},
        msg="sampleRate should accept int 0",
    ),
    DiagnosticTestCase(
        "boundary_int_1",
        setup=[{"profile": 0, "sampleRate": 1}],
        command={"profile": -1},
        checks={"sampleRate": Eq(1.0)},
        msg="sampleRate should accept int 1",
    ),
]

# Property [sampleRate Null No-Op]: setting sampleRate to null does not
# change the current value.
SAMPLERATE_NULL_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "null_noop",
        setup=[
            {"profile": 0, "sampleRate": 0.5},
            {"profile": 0, "sampleRate": None},
        ],
        command={"profile": -1},
        checks={"sampleRate": Eq(0.5)},
        msg="sampleRate should remain 0.5 after setting null",
    ),
]

SAMPLERATE_TESTS = SAMPLERATE_PERSISTENCE_TESTS + SAMPLERATE_BOUNDARY_TESTS + SAMPLERATE_NULL_TESTS


@pytest.mark.parametrize("test", pytest_params(SAMPLERATE_TESTS))
def test_profile_samplerate(collection, test):
    """Test profile sampleRate parameter behavior."""
    for cmd in test.setup:
        execute_command(collection, cmd)
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
    execute_command(collection, {"profile": 0, "sampleRate": 1.0})
