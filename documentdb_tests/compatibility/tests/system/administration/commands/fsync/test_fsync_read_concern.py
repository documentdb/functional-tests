"""Tests for fsync readConcern acceptance and rejection behavior."""

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
    BAD_VALUE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Eq,
    NotExists,
)
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

pytestmark = pytest.mark.no_parallel


# Property [readConcern Level Acceptance]: fsync supports the local read concern
# level; an empty document, a null readConcern, and a null level are all treated
# as absent.
FSYNC_READ_CONCERN_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_level_local",
        command={"fsync": 1, "readConcern": {"level": "local"}},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should accept readConcern level local and perform a no-lock flush",
    ),
    CommandTestCase(
        "read_concern_empty",
        command={"fsync": 1, "readConcern": {}},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should accept an empty readConcern document and perform a no-lock flush",
    ),
    CommandTestCase(
        "read_concern_null",
        command={"fsync": 1, "readConcern": None},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should treat a null readConcern as absent and perform a no-lock flush",
    ),
    CommandTestCase(
        "read_concern_level_null",
        command={"fsync": 1, "readConcern": {"level": None}},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should treat a null readConcern level as absent and perform a no-lock flush",
    ),
]

# Property [readConcern Level Not Supported]: every recognized read concern
# level other than local is rejected with an InvalidOptions error.
FSYNC_READ_CONCERN_LEVEL_REJECTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_level_{level}",
        command={"fsync": 1, "readConcern": {"level": level}},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"fsync should reject readConcern level {level} with an InvalidOptions error",
    )
    for level in ["majority", "available", "linearizable", "snapshot"]
]

# Property [readConcern Invalid Level Value]: a readConcern level string that is
# not a recognized enum value is rejected with a BadValue error.
FSYNC_READ_CONCERN_INVALID_LEVEL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_level_unknown",
        command={"fsync": 1, "readConcern": {"level": "bogus"}},
        error_code=BAD_VALUE_ERROR,
        msg="fsync should reject an unrecognized readConcern level value with a BadValue error",
    ),
]

# Property [readConcern Level Type Strictness]: a readConcern level whose BSON
# type is not a string produces a TypeMismatch error.
FSYNC_READ_CONCERN_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_level_type_{tid}",
        command={"fsync": 1, "readConcern": {"level": val}},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"fsync should reject a {tid} readConcern level with a TypeMismatch error",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(7)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("object", {"a": 1}),
        ("array", ["local"]),
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

# Property [readConcern Type Strictness]: a non-document readConcern produces a
# TypeMismatch error (null is treated as absent, covered by the acceptance
# property).
FSYNC_READ_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_type_{tid}",
        command={"fsync": 1, "readConcern": val},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"fsync should reject a {tid} readConcern value as a non-document "
        "with a TypeMismatch error",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(7)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "local"),
        ("array", [{"level": "local"}]),
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

# Property [readConcern Unknown Sub-Field]: an unrecognized field inside the
# readConcern document produces an unrecognized-field error.
FSYNC_READ_CONCERN_UNKNOWN_SUBFIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_unknown_subfield",
        command={"fsync": 1, "readConcern": {"level": "local", "bogus": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="fsync should reject an unknown sub-field inside readConcern with an "
        "unrecognized-field error",
    ),
]

# Property [readConcern afterClusterTime Sub-field]: afterClusterTime must be a
# Timestamp and is honored only where replication-dependent read concern is
# available.
FSYNC_READ_CONCERN_AFTER_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"read_concern_after_cluster_time_type_{tid}",
            command={"fsync": 1, "readConcern": {"afterClusterTime": val}},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"fsync should reject a {tid} afterClusterTime value with a TypeMismatch error",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(7)),
            ("double", 3.14),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("bool", True),
            ("string", "local"),
            ("null", None),
            ("object", {"a": 1}),
            ("array", [Timestamp(1, 1)]),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "read_concern_after_cluster_time_null_timestamp",
        command={"fsync": 1, "readConcern": {"afterClusterTime": Timestamp(0, 0)}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="fsync should reject a null timestamp (Timestamp(0, 0)) afterClusterTime "
        "with an InvalidOptions error",
    ),
    CommandTestCase(
        "read_concern_after_cluster_time_accepted",
        command={"fsync": 1, "readConcern": {"afterClusterTime": Timestamp(1, 1)}},
        expected={"ok": Eq(1.0), "numFiles": Eq(1), "lockCount": NotExists()},
        msg="fsync should accept a non-zero afterClusterTime and perform a no-lock "
        "flush where replication-dependent read concern is available",
        marks=(pytest.mark.requires(cluster_read_concern=True),),
    ),
    CommandTestCase(
        "read_concern_after_cluster_time_no_replication",
        command={"fsync": 1, "readConcern": {"afterClusterTime": Timestamp(1, 1)}},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="fsync should reject a non-zero afterClusterTime with an IllegalOperation "
        "error where replication-dependent read concern is unavailable",
        marks=(pytest.mark.requires(cluster_read_concern=False),),
    ),
]

# Property [readConcern atClusterTime Sub-field]: atClusterTime must be a
# Timestamp and is rejected because fsync does not support the snapshot level it
# requires.
FSYNC_READ_CONCERN_AT_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"read_concern_at_cluster_time_type_{tid}",
            command={"fsync": 1, "readConcern": {"atClusterTime": val}},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"fsync should reject a {tid} atClusterTime value with a TypeMismatch error",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(7)),
            ("double", 3.14),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("bool", True),
            ("string", "local"),
            ("null", None),
            ("object", {"a": 1}),
            ("array", [Timestamp(1, 1)]),
            ("objectid", ObjectId("507f1f77bcf86cd799439011")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*", "i")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    CommandTestCase(
        "read_concern_at_cluster_time_requires_snapshot",
        command={"fsync": 1, "readConcern": {"atClusterTime": Timestamp(1, 1)}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="fsync should reject an atClusterTime timestamp with an InvalidOptions "
        "error because it requires the unsupported snapshot level",
    ),
]

FSYNC_READ_CONCERN_TESTS: list[CommandTestCase] = (
    FSYNC_READ_CONCERN_ACCEPTED_TESTS
    + FSYNC_READ_CONCERN_LEVEL_REJECTED_TESTS
    + FSYNC_READ_CONCERN_INVALID_LEVEL_TESTS
    + FSYNC_READ_CONCERN_LEVEL_TYPE_ERROR_TESTS
    + FSYNC_READ_CONCERN_TYPE_ERROR_TESTS
    + FSYNC_READ_CONCERN_UNKNOWN_SUBFIELD_TESTS
    + FSYNC_READ_CONCERN_AFTER_CLUSTER_TIME_TESTS
    + FSYNC_READ_CONCERN_AT_CLUSTER_TIME_TESTS
)


@pytest.mark.parametrize("test", pytest_params(FSYNC_READ_CONCERN_TESTS))
def test_fsync_read_concern_cases(collection, test):
    """Test fsync readConcern acceptance and rejection cases."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
