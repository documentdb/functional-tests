"""Tests for killCursors cursors field acceptance."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MIN,
    INT32_OVERFLOW,
    INT32_UNDERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
    INT64_ZERO,
)

# Property [Int64 Boundary Values]: Int64 boundary values are accepted in
# the cursors array and reported in cursorsNotFound when they do not match
# an active cursor.
KILLCURSORS_INT64_BOUNDARY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"boundary_{tid}",
        command=lambda ctx, v=val: {
            "killCursors": ctx.collection,
            "cursors": [v],
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [val],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg=f"killCursors should accept Int64 {tid}",
    )
    for tid, val in [
        ("zero", INT64_ZERO),
        ("positive_one", Int64(1)),
        ("negative_one", Int64(-1)),
        ("int32_max", Int64(INT32_MAX)),
        ("int32_min", Int64(INT32_MIN)),
        ("int32_max_plus_one", Int64(INT32_OVERFLOW)),
        ("int32_min_minus_one", Int64(INT32_UNDERFLOW)),
        ("int64_max", INT64_MAX),
        ("int64_min", INT64_MIN),
        ("int64_max_minus_one", INT64_MAX_MINUS_1),
        ("int64_min_plus_one", INT64_MIN_PLUS_1),
    ]
]

# Property [Null Element Silent Skip]: null elements in the cursors array
# are silently skipped without triggering type-validation rejection, and
# valid Int64 elements alongside nulls are still processed normally.
KILLCURSORS_NULL_ELEMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_element_interspersed_with_valid",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [None, Int64(1), None, Int64(2), None],
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(1), Int64(2)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should process valid Int64 elements and skip interspersed nulls",
    ),
]

# Property [cursors Field Empty Array]: an empty cursors array is a valid
# no-op that succeeds with ok 1.0 and all response arrays empty.
KILLCURSORS_EMPTY_ARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_array_noop",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [],
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should succeed as a no-op with an empty cursors array",
    ),
]

# Property [cursors Field Array Size]: large arrays are accepted,
# limited only by the 16MB BSON document size.
KILLCURSORS_LARGE_ARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "large_array_10k",
        command=lambda ctx: {
            "killCursors": ctx.collection,
            "cursors": [Int64(i) for i in range(10_000)],
        },
        expected={
            "cursorsKilled": [],
            "cursorsNotFound": [Int64(i) for i in range(10_000)],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        msg="killCursors should accept a cursors array with 10,000 elements",
    ),
]

KILLCURSORS_CURSORS_ACCEPTANCE_TESTS: list[CommandTestCase] = (
    KILLCURSORS_INT64_BOUNDARY_TESTS
    + KILLCURSORS_NULL_ELEMENT_TESTS
    + KILLCURSORS_EMPTY_ARRAY_TESTS
    + KILLCURSORS_LARGE_ARRAY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLCURSORS_CURSORS_ACCEPTANCE_TESTS))
def test_killCursors_cursors_acceptance(collection, test):
    """Test killCursors cursors field acceptance."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
