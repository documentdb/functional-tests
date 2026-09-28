"""Tests for fsync lock acquisition, coercion, nesting, and persistence."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    Exists,
    IsType,
    NotExists,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_HALF,
    DOUBLE_NEGATIVE_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT32_ZERO,
    INT64_ZERO,
)

pytestmark = pytest.mark.no_parallel


# Property [Lock Coercion - Falsy]: boolean false and any zero-magnitude numeric
# (including negative zero) coerce to false, acquiring no lock.
FSYNC_LOCK_FALSY_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"lock_falsy_{tid}",
            command={"fsync": 1, "lock": val},
            expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
            msg=f"fsync should treat a {tid} lock value as falsy and acquire no lock",
        )
        for tid, val in [
            ("int_zero", INT32_ZERO),
            ("int64_zero", INT64_ZERO),
            ("double_zero", DOUBLE_ZERO),
            ("double_negative_zero", DOUBLE_NEGATIVE_ZERO),
            ("decimal_zero", DECIMAL128_ZERO),
            ("decimal_negative_zero", DECIMAL128_NEGATIVE_ZERO),
        ]
    ],
    CommandTestCase(
        "lock_falsy_bool_false",
        command={"fsync": 1, "lock": False},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should treat a boolean false lock value as falsy and acquire no lock",
    ),
    CommandTestCase(
        "lock_falsy_with_timeout",
        command={"fsync": 1, "lock": False, "fsyncLockAcquisitionTimeoutMillis": 5_000},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should perform a no-lock flush when lock is false even with a "
        "timeout present",
    ),
]

# Property [Lock Acquisition and Response Shape]: a truthy lock acquires an
# fsync lock and returns info, an Int64 lockCount, and seeAlso with no numFiles;
# options supplied alongside lock do not alter the response.
FSYNC_LOCK_ACQUISITION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "lock_true",
        command={"fsync": 1, "lock": True},
        expected={
            "info": Eq("now locked against writes, use db.fsyncUnlock() to unlock"),
            "lockCount": [IsType("long"), Eq(Int64(1))],
            "seeAlso": [Exists(), IsType("string")],
            "ok": Eq(1.0),
            "numFiles": NotExists(),
        },
        msg="fsync should acquire a lock and return the lock response shape",
    ),
    CommandTestCase(
        "lock_true_with_options",
        command={
            "fsync": 1,
            "lock": True,
            "comment": "lock with options",
            "fsyncLockAcquisitionTimeoutMillis": 90_000,
        },
        expected={
            "info": [Exists(), IsType("string")],
            "lockCount": [IsType("long"), Eq(Int64(1))],
            "seeAlso": [Exists(), IsType("string")],
            "ok": Eq(1.0),
            "numFiles": NotExists(),
            "comment": NotExists(),
        },
        msg="fsync should acquire a lock when comment and timeout are also present",
    ),
]

# Property [Lock Coercion - Truthy]: any non-zero-magnitude numeric (including
# NaN and signed infinity) coerces to true and acquires a lock.
FSYNC_LOCK_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"lock_truthy_{tid}",
        command={"fsync": 1, "lock": val},
        expected={
            "ok": Eq(1.0),
            "lockCount": [IsType("long"), Eq(Int64(1))],
            "numFiles": NotExists(),
        },
        msg=f"fsync should treat a {tid} lock value as truthy and acquire a lock",
    )
    for tid, val in [
        ("int_positive", 1),
        ("int64_positive", Int64(2)),
        ("double_positive", DOUBLE_HALF),
        ("double_negative", DOUBLE_NEGATIVE_ONE_AND_HALF),
        ("decimal_positive", DECIMAL128_ONE_AND_HALF),
        ("decimal_negative", DECIMAL128_NEGATIVE_ONE_AND_HALF),
        ("double_nan", FLOAT_NAN),
        ("decimal_nan", DECIMAL128_NAN),
        ("double_infinity", FLOAT_INFINITY),
        ("double_negative_infinity", FLOAT_NEGATIVE_INFINITY),
        ("decimal_infinity", DECIMAL128_INFINITY),
        ("decimal_negative_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [Timeout Value Accepted With Lock]: any int32
# fsyncLockAcquisitionTimeoutMillis, including zero, negatives, and the int32
# extremes, is accepted with no value-range validation.
FSYNC_TIMEOUT_WITH_LOCK_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"timeout_with_lock_{tid}",
        command={
            "fsync": 1,
            "lock": True,
            "fsyncLockAcquisitionTimeoutMillis": val,
        },
        expected={
            "ok": Eq(1.0),
            "lockCount": [IsType("long"), Eq(Int64(1))],
            "numFiles": NotExists(),
        },
        msg=f"fsync should accept a {tid} timeout value and still acquire the lock",
    )
    for tid, val in [
        ("zero", INT32_ZERO),
        ("one", 1),
        ("negative_one", -1),
        ("int32_max", INT32_MAX),
        ("int32_min", INT32_MIN),
    ]
]

FSYNC_LOCK_TESTS: list[CommandTestCase] = (
    FSYNC_LOCK_FALSY_TESTS
    + FSYNC_LOCK_ACQUISITION_TESTS
    + FSYNC_LOCK_TRUTHY_TESTS
    + FSYNC_TIMEOUT_WITH_LOCK_TESTS
)


@pytest.mark.parametrize("test", pytest_params(FSYNC_LOCK_TESTS))
def test_fsync_lock_cases(collection, test):
    """Test fsync lock coercion, acquisition, and response-shape cases."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Lock Counting and Nesting]: a lock:true issued while the lock is
# already held nests rather than conflicting, returning a lockCount one higher
# than the existing depth.
def test_fsync_lock_nesting_increments_count(collection):
    """Test fsync lock:true returns an incremented lockCount when already locked."""
    # Precondition: hold the lock twice so the command under test is the third.
    execute_admin_command(collection, {"fsync": 1, "lock": True})
    execute_admin_command(collection, {"fsync": 1, "lock": True})
    result = execute_admin_command(collection, {"fsync": 1, "lock": True})
    assertResult(
        result,
        expected={"ok": Eq(1.0), "lockCount": [IsType("long"), Eq(Int64(3))]},
        msg="fsync should nest a lock while already held, returning lockCount 3",
        raw_res=True,
    )


# Property [Lock Persistence Across Connection Close]: the server-global lock
# persists when the acquiring connection closes without unlocking, so a fresh
# lock:true returns lockCount 2 rather than 1.
def test_fsync_lock_persists_after_connection_close(connection_string, collection):
    """Test fsync lock persists after the acquiring connection closes."""
    # Precondition: acquire the lock on a separate connection, then close that
    # connection without unlocking.
    second_client = fixtures.create_engine_client(connection_string, "second")
    second_coll = second_client[collection.database.name][collection.name]
    execute_admin_command(second_coll, {"fsync": 1, "lock": True})
    second_client.close()
    # If the lock had been released on disconnect this would return lockCount 1;
    # lockCount 2 proves the lock survived the close.
    result = execute_admin_command(collection, {"fsync": 1, "lock": True})
    assertResult(
        result,
        expected={"ok": Eq(1.0), "lockCount": [IsType("long"), Eq(Int64(2))]},
        msg="fsync should still see the lock held after the acquiring connection "
        "closes, returning lockCount 2",
        raw_res=True,
    )
