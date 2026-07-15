"""Tests for fsync no-lock flush behavior and response shape."""

from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import CommandTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    IsType,
    NotExists,
)
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

pytestmark = pytest.mark.no_parallel


# Property [Null and Missing Behavior]: a null or missing value in any field is
# treated as absent, performing a no-lock flush.
FSYNC_NULL_MISSING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "fsync_key_null",
        command={"fsync": None},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should perform a no-lock flush when the command-key value is null",
    ),
    CommandTestCase(
        "lock_null",
        command={"fsync": 1, "lock": None},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should perform a no-lock flush when lock is null",
    ),
    CommandTestCase(
        "timeout_null",
        command={"fsync": 1, "fsyncLockAcquisitionTimeoutMillis": None},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should perform a no-lock flush when "
        "fsyncLockAcquisitionTimeoutMillis is null",
    ),
    CommandTestCase(
        "comment_null",
        command={"fsync": 1, "comment": None},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should perform a no-lock flush when comment is null",
    ),
    CommandTestCase(
        "all_fields_null",
        command={
            "fsync": None,
            "lock": None,
            "fsyncLockAcquisitionTimeoutMillis": None,
            "comment": None,
        },
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should perform a no-lock flush when every field is null",
    ),
    CommandTestCase(
        "optional_fields_missing",
        command={"fsync": 1},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should perform a no-lock flush when all optional fields are omitted",
    ),
]

# Property [Flush Response Shape]: a no-lock flush returns an integer numFiles
# and none of the lock-only fields.
FSYNC_FLUSH_SHAPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "flush_shape",
        command={"fsync": 1},
        expected={
            "ok": Eq(1.0),
            "numFiles": IsType("int"),
            "lockCount": NotExists(),
            "info": NotExists(),
            "seeAlso": NotExists(),
        },
        msg="fsync should return an integer numFiles and no lock-only fields on a no-lock flush",
    ),
]

# Property [Command-Key Value Ignored]: the fsync command-key value is never
# type-validated.
FSYNC_KEY_IGNORED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"key_{tid}",
        command={"fsync": val},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg=f"fsync should ignore a {tid} command-key value and perform a no-lock flush",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(7)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "flush"),
        ("object", {"a": 1}),
        ("array", [1, 2, 3]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Timeout Value Without Lock]: fsyncLockAcquisitionTimeoutMillis is
# accepted and has no effect when no lock is requested.
FSYNC_TIMEOUT_NO_LOCK_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timeout_no_lock",
        command={"fsync": 1, "fsyncLockAcquisitionTimeoutMillis": 5_000},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should accept a timeout value without lock and perform a no-lock flush",
    ),
]

FSYNC_NO_LOCK_FLUSH_TESTS: list[CommandTestCase] = (
    FSYNC_NULL_MISSING_TESTS
    + FSYNC_FLUSH_SHAPE_TESTS
    + FSYNC_KEY_IGNORED_TESTS
    + FSYNC_TIMEOUT_NO_LOCK_TESTS
)


@pytest.mark.parametrize("test", pytest_params(FSYNC_NO_LOCK_FLUSH_TESTS))
def test_fsync_no_lock_flush_cases(collection, test):
    """Test fsync no-lock flush success and response-shape cases."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
