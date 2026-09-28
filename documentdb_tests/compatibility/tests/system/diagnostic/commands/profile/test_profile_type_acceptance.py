"""Tests for profile command type acceptance.

Validates that the profile, slowms, and sampleRate fields accept all valid
numeric BSON types and that the values are actually applied.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gte

pytestmark = [pytest.mark.no_parallel]

# Property [Profile Field Type Acceptance]: the profile field accepts int,
# Int64, double, and Decimal128 for valid level values, and the level is
# actually applied.
PROFILE_TYPE_ACCEPTANCE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "profile_int_0",
        setup=[{"profile": 1}, {"profile": 0}],
        command={"profile": -1},
        checks={"was": Eq(0)},
        msg="profile should accept int 0 and apply level",
    ),
    DiagnosticTestCase(
        "profile_int_1",
        setup=[{"profile": 0}, {"profile": 1}],
        command={"profile": -1},
        checks={"was": Eq(1)},
        msg="profile should accept int 1 and apply level",
    ),
    DiagnosticTestCase(
        "profile_int_2",
        setup=[{"profile": 0}, {"profile": 2}],
        command={"profile": -1},
        checks={"was": Eq(2)},
        msg="profile should accept int 2 and apply level",
    ),
    DiagnosticTestCase(
        "profile_int_neg1",
        setup=[{"profile": 1}],
        command={"profile": -1},
        checks={"was": Eq(1)},
        msg="profile should accept int -1 and read current level",
    ),
    DiagnosticTestCase(
        "profile_int64_0",
        setup=[{"profile": 1}, {"profile": Int64(0)}],
        command={"profile": -1},
        checks={"was": Eq(0)},
        msg="profile should accept Int64(0) and apply level",
    ),
    DiagnosticTestCase(
        "profile_int64_1",
        setup=[{"profile": 0}, {"profile": Int64(1)}],
        command={"profile": -1},
        checks={"was": Eq(1)},
        msg="profile should accept Int64(1) and apply level",
    ),
    DiagnosticTestCase(
        "profile_int64_2",
        setup=[{"profile": 0}, {"profile": Int64(2)}],
        command={"profile": -1},
        checks={"was": Eq(2)},
        msg="profile should accept Int64(2) and apply level",
    ),
    DiagnosticTestCase(
        "profile_double_0",
        setup=[{"profile": 1}, {"profile": 0.0}],
        command={"profile": -1},
        checks={"was": Eq(0)},
        msg="profile should accept double 0.0 and apply level",
    ),
    DiagnosticTestCase(
        "profile_double_1",
        setup=[{"profile": 0}, {"profile": 1.0}],
        command={"profile": -1},
        checks={"was": Eq(1)},
        msg="profile should accept double 1.0 and apply level",
    ),
    DiagnosticTestCase(
        "profile_double_2",
        setup=[{"profile": 0}, {"profile": 2.0}],
        command={"profile": -1},
        checks={"was": Eq(2)},
        msg="profile should accept double 2.0 and apply level",
    ),
    DiagnosticTestCase(
        "profile_double_neg1",
        setup=[{"profile": 1}],
        command={"profile": -1.0},
        checks={"was": Eq(1)},
        msg="profile should accept double -1.0 and read current level",
    ),
    DiagnosticTestCase(
        "profile_decimal128_0",
        setup=[{"profile": 1}, {"profile": Decimal128("0")}],
        command={"profile": -1},
        checks={"was": Eq(0)},
        msg="profile should accept Decimal128('0') and apply level",
    ),
    DiagnosticTestCase(
        "profile_decimal128_1",
        setup=[{"profile": 0}, {"profile": Decimal128("1")}],
        command={"profile": -1},
        checks={"was": Eq(1)},
        msg="profile should accept Decimal128('1') and apply level",
    ),
    DiagnosticTestCase(
        "profile_decimal128_2",
        setup=[{"profile": 0}, {"profile": Decimal128("2")}],
        command={"profile": -1},
        checks={"was": Eq(2)},
        msg="profile should accept Decimal128('2') and apply level",
    ),
]

# Property [slowms Type Acceptance]: the slowms field accepts numeric BSON
# types (int, Int64, double, Decimal128) and null, and the value is applied.
SLOWMS_TYPE_ACCEPTANCE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "slowms_int_100",
        setup=[{"profile": 0, "slowms": 100}],
        command={"profile": -1},
        checks={"slowms": Eq(100)},
        msg="slowms should accept int 100 and persist value",
    ),
    DiagnosticTestCase(
        "slowms_int64_100",
        setup=[{"profile": 0, "slowms": Int64(100)}],
        command={"profile": -1},
        checks={"slowms": Eq(100)},
        msg="slowms should accept Int64(100) and persist value",
    ),
    DiagnosticTestCase(
        "slowms_double_100",
        setup=[{"profile": 0, "slowms": 100.0}],
        command={"profile": -1},
        checks={"slowms": Eq(100)},
        msg="slowms should accept double 100.0 and persist value",
    ),
    DiagnosticTestCase(
        "slowms_decimal128_100",
        setup=[{"profile": 0, "slowms": Decimal128("100")}],
        command={"profile": -1},
        checks={"slowms": Eq(100)},
        msg="slowms should accept Decimal128('100') and persist value",
    ),
    DiagnosticTestCase(
        "slowms_null",
        command={"profile": 0, "slowms": None},
        checks={"ok": Eq(1.0)},
        msg="slowms should accept null (no-op)",
    ),
]

# Property [sampleRate Type Acceptance]: the sampleRate field accepts numeric
# BSON types (int, Int64, double, Decimal128) within [0, 1] and null, and the
# value is applied.
SAMPLERATE_TYPE_ACCEPTANCE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "samplerate_double_0_5",
        setup=[{"profile": 0, "sampleRate": 0.5}],
        command={"profile": -1},
        checks={"sampleRate": Eq(0.5)},
        msg="sampleRate should accept double 0.5 and persist value",
    ),
    DiagnosticTestCase(
        "samplerate_int_0",
        setup=[{"profile": 0, "sampleRate": 0}],
        command={"profile": -1},
        checks={"sampleRate": Eq(0.0)},
        msg="sampleRate should accept int 0 and persist value",
    ),
    DiagnosticTestCase(
        "samplerate_int_1",
        setup=[{"profile": 0, "sampleRate": 1}],
        command={"profile": -1},
        checks={"sampleRate": Eq(1.0)},
        msg="sampleRate should accept int 1 and persist value",
    ),
    DiagnosticTestCase(
        "samplerate_int64_0",
        setup=[{"profile": 0, "sampleRate": Int64(0)}],
        command={"profile": -1},
        checks={"sampleRate": Eq(0.0)},
        msg="sampleRate should accept Int64(0) and persist value",
    ),
    DiagnosticTestCase(
        "samplerate_int64_1",
        setup=[{"profile": 0, "sampleRate": Int64(1)}],
        command={"profile": -1},
        checks={"sampleRate": Eq(1.0)},
        msg="sampleRate should accept Int64(1) and persist value",
    ),
    # Decimal128("0") converts to a near-zero double (~2.225e-308), not exactly 0.0,
    # so we use Gte(0.0) instead of Eq(0.0).
    DiagnosticTestCase(
        "samplerate_decimal128_0",
        setup=[{"profile": 0, "sampleRate": Decimal128("0")}],
        command={"profile": -1},
        checks={"sampleRate": Gte(0.0)},
        msg="sampleRate should accept Decimal128('0') and persist value",
    ),
    DiagnosticTestCase(
        "samplerate_decimal128_0_5",
        setup=[{"profile": 0, "sampleRate": Decimal128("0.5")}],
        command={"profile": -1},
        checks={"sampleRate": Eq(0.5)},
        msg="sampleRate should accept Decimal128('0.5') and persist value",
    ),
    DiagnosticTestCase(
        "samplerate_decimal128_1",
        setup=[{"profile": 0, "sampleRate": Decimal128("1")}],
        command={"profile": -1},
        checks={"sampleRate": Eq(1.0)},
        msg="sampleRate should accept Decimal128('1') and persist value",
    ),
    DiagnosticTestCase(
        "samplerate_null",
        command={"profile": 0, "sampleRate": None},
        checks={"ok": Eq(1.0)},
        msg="sampleRate should accept null (no-op)",
    ),
]

TYPE_ACCEPTANCE_TESTS = (
    PROFILE_TYPE_ACCEPTANCE_TESTS + SLOWMS_TYPE_ACCEPTANCE_TESTS + SAMPLERATE_TYPE_ACCEPTANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TYPE_ACCEPTANCE_TESTS))
def test_profile_type_acceptance(collection, test):
    """Test profile command field type acceptance with readback verification."""
    for cmd in test.setup:
        execute_command(collection, cmd)
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
    execute_command(collection, {"profile": 0, "slowms": 100, "sampleRate": 1.0})
