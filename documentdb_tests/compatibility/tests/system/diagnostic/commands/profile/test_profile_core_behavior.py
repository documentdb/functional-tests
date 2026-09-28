"""Tests for profile command core behavior.

Validates profiling level transitions, the 'was' field, out-of-range levels,
fractional level read-back, idempotency, and level persistence via read.
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

# Property [Was Field Transitions]: the 'was' field returns the profiling
# level that was active before the current command.
WAS_TRANSITION_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "was_0_to_1",
        setup=[{"profile": 0}],
        command={"profile": 1},
        checks={"was": Eq(0)},
        msg="'was' should be 0 after transition 0->1",
    ),
    DiagnosticTestCase(
        "was_1_to_2",
        setup=[{"profile": 1}],
        command={"profile": 2},
        checks={"was": Eq(1)},
        msg="'was' should be 1 after transition 1->2",
    ),
    DiagnosticTestCase(
        "was_2_to_0",
        setup=[{"profile": 2}],
        command={"profile": 0},
        checks={"was": Eq(2)},
        msg="'was' should be 2 after transition 2->0",
    ),
    DiagnosticTestCase(
        "was_0_to_0",
        setup=[{"profile": 0}],
        command={"profile": 0},
        checks={"was": Eq(0)},
        msg="'was' should be 0 after transition 0->0",
    ),
]

# Property [Level Persistence via Read]: reading with -1 returns the current
# level in the 'was' field.
LEVEL_READ_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "read_level_0",
        setup=[{"profile": 0}],
        command={"profile": -1},
        checks={"was": Eq(0)},
        msg="'was' should be 0 when reading at level 0",
    ),
    DiagnosticTestCase(
        "read_level_1",
        setup=[{"profile": 1}],
        command={"profile": -1},
        checks={"was": Eq(1)},
        msg="'was' should be 1 when reading at level 1",
    ),
    DiagnosticTestCase(
        "read_level_2",
        setup=[{"profile": 2}],
        command={"profile": -1},
        checks={"was": Eq(2)},
        msg="'was' should be 2 when reading at level 2",
    ),
]

# Property [Out-of-Range Levels]: integer levels outside {-1, 0, 1, 2}
# succeed but do not change the profiling level.
OUT_OF_RANGE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "out_of_range_3",
        setup=[{"profile": 1}, {"profile": 3}],
        command={"profile": -1},
        checks={"was": Eq(1)},
        msg="profile level 3 should be a no-op",
    ),
    DiagnosticTestCase(
        "out_of_range_neg2",
        setup=[{"profile": 2}, {"profile": -2}],
        command={"profile": -1},
        checks={"was": Eq(2)},
        msg="profile level -2 should be a no-op",
    ),
    DiagnosticTestCase(
        "out_of_range_100",
        setup=[{"profile": 0}, {"profile": 100}],
        command={"profile": -1},
        checks={"was": Eq(0)},
        msg="profile level 100 should be a no-op",
    ),
]

# Property [Fractional Level Read-Back]: after setting a fractional level,
# reading with -1 returns the truncated integer level.
FRACTIONAL_READBACK_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "readback_1_5",
        setup=[{"profile": 0}, {"profile": 1.5}],
        command={"profile": -1},
        checks={"was": Eq(1)},
        msg="profile 1.5 should read back as level 1",
    ),
    DiagnosticTestCase(
        "readback_0_5",
        setup=[{"profile": 0}, {"profile": 0.5}],
        command={"profile": -1},
        checks={"was": Eq(0)},
        msg="profile 0.5 should read back as level 0",
    ),
    DiagnosticTestCase(
        "readback_2_9",
        setup=[{"profile": 0}, {"profile": 2.9}],
        command={"profile": -1},
        checks={"was": Eq(2)},
        msg="profile 2.9 should read back as level 2",
    ),
]

# Property [Idempotency]: repeated identical profile commands produce
# consistent results.
IDEMPOTENCY_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "idempotent_set_0",
        setup=[{"profile": 0}],
        command={"profile": 0},
        checks={"was": Eq(0), "ok": Eq(1.0)},
        msg="Second profile 0 should show was=0",
    ),
]

CORE_BEHAVIOR_TESTS = (
    WAS_TRANSITION_TESTS
    + LEVEL_READ_TESTS
    + OUT_OF_RANGE_TESTS
    + FRACTIONAL_READBACK_TESTS
    + IDEMPOTENCY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CORE_BEHAVIOR_TESTS))
def test_profile_core_behavior(collection, test):
    """Test profile command core behavior."""
    for cmd in test.setup:
        execute_command(collection, cmd)
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
    execute_command(collection, {"profile": 0})


def test_profile_idempotent_read(collection):
    """Test running profile -1 twice returns identical results."""
    execute_command(collection, {"profile": 0})
    result1 = execute_command(collection, {"profile": -1})
    result2 = execute_command(collection, {"profile": -1})
    assertProperties(
        result2,
        {
            "was": Eq(result1["was"]),
            "slowms": Eq(result1["slowms"]),
            "sampleRate": Eq(result1["sampleRate"]),
        },
        msg="Two consecutive reads should return identical results",
        raw_res=True,
    )
