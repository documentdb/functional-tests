"""Tests for killAllSessions maxTimeMS, readConcern, writeConcern, and Stable API acceptance."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT32_MAX,
    INT64_ZERO,
)

pytestmark = pytest.mark.no_parallel

# Property [maxTimeMS Acceptance]: maxTimeMS accepts numeric types in
# range [0, INT32_MAX].
KILLALLSESSIONS_MAXTIMEMS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [], "maxTimeMS": v},
        expected={"ok": 1.0},
        msg=f"killAllSessions should accept {tid} maxTimeMS",
    )
    for tid, val in [
        ("int32_zero", 0),
        ("int64_zero", INT64_ZERO),
        ("double_zero", DOUBLE_ZERO),
        ("double_negative_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_zero", DECIMAL128_ZERO),
        ("decimal128_negative_zero", DECIMAL128_NEGATIVE_ZERO),
        ("int32_positive", 1000),
        ("int64_positive", Int64(1000)),
        ("double_positive", 1000.0),
        ("decimal128_positive", Decimal128("1000")),
        ("int32_max", INT32_MAX),
        ("int64_max", Int64(INT32_MAX)),
        ("double_max", float(INT32_MAX)),
        ("decimal128_max", Decimal128(str(INT32_MAX))),
        ("null", None),
    ]
]

# Property [readConcern Acceptance]: valid readConcern values are accepted.
KILLALLSESSIONS_READCONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_empty_doc",
        command=lambda ctx: {"killAllSessions": [], "readConcern": {}},
        expected={"ok": 1.0},
        msg="killAllSessions should accept empty readConcern document",
    ),
    CommandTestCase(
        "readconcern_null",
        command=lambda ctx: {"killAllSessions": [], "readConcern": None},
        expected={"ok": 1.0},
        msg="killAllSessions should accept null readConcern",
    ),
    CommandTestCase(
        "readconcern_local",
        command=lambda ctx: {"killAllSessions": [], "readConcern": {"level": "local"}},
        expected={"ok": 1.0},
        msg="killAllSessions should accept readConcern with level local",
    ),
    CommandTestCase(
        "readconcern_level_null",
        command=lambda ctx: {"killAllSessions": [], "readConcern": {"level": None}},
        expected={"ok": 1.0},
        msg="killAllSessions should accept readConcern with null level",
    ),
]

# Property [writeConcern Null Acceptance]: null writeConcern is treated
# as omitted.
KILLALLSESSIONS_WRITECONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_null",
        command=lambda ctx: {"killAllSessions": [], "writeConcern": None},
        expected={"ok": 1.0},
        msg="killAllSessions should accept null writeConcern",
    ),
]

# Property [Stable API Acceptance]: killAllSessions is accepted with
# apiVersion "1" when apiStrict is not true.
KILLALLSESSIONS_API_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "api_version_1",
        command=lambda ctx: {"killAllSessions": [], "apiVersion": "1"},
        expected={"ok": 1.0},
        msg="killAllSessions should accept apiVersion 1",
    ),
    CommandTestCase(
        "api_version_1_strict_false",
        command=lambda ctx: {
            "killAllSessions": [],
            "apiVersion": "1",
            "apiStrict": False,
        },
        expected={"ok": 1.0},
        msg="killAllSessions should accept apiVersion 1 with apiStrict false",
    ),
    CommandTestCase(
        "api_version_1_deprecation_true",
        command=lambda ctx: {
            "killAllSessions": [],
            "apiVersion": "1",
            "apiDeprecationErrors": True,
        },
        expected={"ok": 1.0},
        msg="killAllSessions should accept apiVersion 1 with apiDeprecationErrors true",
    ),
    CommandTestCase(
        "api_version_1_deprecation_false",
        command=lambda ctx: {
            "killAllSessions": [],
            "apiVersion": "1",
            "apiDeprecationErrors": False,
        },
        expected={"ok": 1.0},
        msg="killAllSessions should accept apiVersion 1 with apiDeprecationErrors false",
    ),
]

KILLALLSESSIONS_OPTIONS_TESTS: list[CommandTestCase] = (
    KILLALLSESSIONS_MAXTIMEMS_ACCEPTANCE_TESTS
    + KILLALLSESSIONS_READCONCERN_ACCEPTANCE_TESTS
    + KILLALLSESSIONS_WRITECONCERN_ACCEPTANCE_TESTS
    + KILLALLSESSIONS_API_ACCEPTANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLALLSESSIONS_OPTIONS_TESTS))
def test_killAllSessions_options(collection, test):
    """Test killAllSessions option field acceptance."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
