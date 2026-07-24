"""Tests for fsync lock and timeout field type strictness."""

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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

pytestmark = pytest.mark.no_parallel


# Property [lock Type Strictness]: a non-numeric lock value produces a
# TypeMismatch error, and a literal array is not unwrapped.
FSYNC_LOCK_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"lock_type_{tid}",
            command={"fsync": 1, "lock": val},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"fsync should reject a {tid} lock value with a TypeMismatch error",
        )
        for tid, val in [
            ("string", "x"),
            ("object", {"a": 1}),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "lock_array_true",
        command={"fsync": 1, "lock": [True]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync should reject a single-element truthy array lock value without unwrapping it",
    ),
    CommandTestCase(
        "lock_array_false",
        command={"fsync": 1, "lock": [False]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="fsync should reject a single-element falsy array lock value without unwrapping it",
    ),
]

# Property [fsyncLockAcquisitionTimeoutMillis Type Strictness]: a non-int32
# timeout produces a TypeMismatch error with no coercion, and a literal array is
# not unwrapped.
FSYNC_TIMEOUT_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"timeout_type_{tid}",
        command={"fsync": 1, "fsyncLockAcquisitionTimeoutMillis": val},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"fsync should reject a {tid} timeout value with a TypeMismatch error",
    )
    for tid, val in [
        ("int64", Int64(100)),
        ("double_whole", 90_000.0),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "90000"),
        ("object", {"a": 1}),
        ("array", [42]),
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

FSYNC_LOCK_TIMEOUT_TYPE_ERROR_TESTS: list[CommandTestCase] = (
    FSYNC_LOCK_TYPE_ERROR_TESTS + FSYNC_TIMEOUT_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(FSYNC_LOCK_TIMEOUT_TYPE_ERROR_TESTS))
def test_fsync_lock_timeout_type_error_cases(collection, test):
    """Test fsync lock and timeout type-strictness error cases."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
