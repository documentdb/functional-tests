"""Tests for fsync writeConcern rejection and type strictness."""

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
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    NotExists,
)
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

pytestmark = pytest.mark.no_parallel


# Property [writeConcern Not Supported]: fsync does not support writeConcern, so
# a writeConcern document is rejected with an InvalidOptions error regardless of
# its sub-fields (a null writeConcern is treated as absent, covered separately).
FSYNC_WRITE_CONCERN_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"write_concern_{tid}",
        command={"fsync": 1, "writeConcern": val},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"fsync should reject a writeConcern document ({tid}) with an InvalidOptions error",
    )
    for tid, val in [
        ("empty", {}),
        ("w_one", {"w": 1}),
        ("w_zero", {"w": 0}),
        ("w_majority", {"w": "majority"}),
        ("j_true", {"j": True}),
        ("wtimeout", {"w": 1, "wtimeout": 1_000}),
    ]
]

# Property [writeConcern Type Strictness]: a non-document writeConcern produces a
# TypeMismatch error.
FSYNC_WRITE_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"write_concern_type_{tid}",
        command={"fsync": 1, "writeConcern": val},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"fsync should reject a {tid} writeConcern value as a non-document "
        "with a TypeMismatch error",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(7)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "majority"),
        ("array", [{"w": 1}]),
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

# Property [writeConcern Null Treated As Absent]: a null writeConcern is ignored
# rather than triggering the unsupported-option rejection.
FSYNC_WRITE_CONCERN_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "write_concern_null",
        command={"fsync": 1, "writeConcern": None},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should treat a null writeConcern as absent and perform a no-lock flush",
    ),
]

FSYNC_WRITE_CONCERN_TESTS: list[CommandTestCase] = (
    FSYNC_WRITE_CONCERN_REJECTED_TESTS
    + FSYNC_WRITE_CONCERN_TYPE_ERROR_TESTS
    + FSYNC_WRITE_CONCERN_NULL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(FSYNC_WRITE_CONCERN_TESTS))
def test_fsync_write_concern_cases(collection, test):
    """Test fsync writeConcern rejection, type-strictness, and null-as-absent cases."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
