"""Tests for getDefaultRWConcern command input acceptance and rejection behavior."""

from datetime import datetime, timezone

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [readConcern Acceptance]: the command accepts a readConcern that
# resolves to the supported local level.
GETDEFAULTRWCONCERN_READ_CONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_local",
        command={"getDefaultRWConcern": 1, "readConcern": {"level": "local"}},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should accept a readConcern with level local",
    ),
    CommandTestCase(
        "read_concern_empty",
        command={"getDefaultRWConcern": 1, "readConcern": {}},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should accept an empty readConcern object",
    ),
    CommandTestCase(
        "read_concern_level_null",
        command={"getDefaultRWConcern": 1, "readConcern": {"level": None}},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should treat a null readConcern level as the default and succeed",
    ),
    CommandTestCase(
        "read_concern_after_cluster_time",
        command={"getDefaultRWConcern": 1, "readConcern": {"afterClusterTime": Timestamp(1, 1)}},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should accept a readConcern with afterClusterTime",
    ),
]

# Property [readConcern Type Errors]: a non-object, non-null readConcern is
# rejected by the object type check.
GETDEFAULTRWCONCERN_READ_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_type_{tid}",
        command={"getDefaultRWConcern": 1, "readConcern": val},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getDefaultRWConcern should reject a {tid} readConcern as a non-object",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(2)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "local"),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("array", [1]),
    ]
]

# Property [readConcern level Type Errors]: a non-string, non-null readConcern
# level is rejected by the type check.
GETDEFAULTRWCONCERN_READ_CONCERN_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_level_type_{tid}",
        command={"getDefaultRWConcern": 1, "readConcern": {"level": val}},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getDefaultRWConcern should reject a {tid} readConcern level as a non-string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(2)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("array", ["local"]),
        ("object", {"a": 1}),
    ]
]

# Property [readConcern level Value Errors]: a string readConcern level that is
# not a recognized value is rejected.
GETDEFAULTRWCONCERN_READ_CONCERN_LEVEL_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_level_value_{tid}",
        command={"getDefaultRWConcern": 1, "readConcern": {"level": val}},
        error_code=BAD_VALUE_ERROR,
        msg=f"getDefaultRWConcern should reject a {tid} readConcern level value",
    )
    for tid, val in [
        ("empty", ""),
        ("unknown", "bogus"),
        ("wrong_case", "LOCAL"),
    ]
]

# Property [Unsupported readConcern Levels]: recognized read concern levels
# other than local are rejected as unsupported.
GETDEFAULTRWCONCERN_READ_CONCERN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_{level}",
        command={"getDefaultRWConcern": 1, "readConcern": {"level": level}},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"getDefaultRWConcern should reject the {level} read concern level",
    )
    for level in ["available", "majority", "linearizable", "snapshot"]
]

# Property [readConcern atClusterTime]: atClusterTime is only valid with a
# snapshot level, so supplying it without one is rejected.
GETDEFAULTRWCONCERN_READ_CONCERN_AT_CLUSTER_TIME_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_at_cluster_time_without_snapshot",
        command={"getDefaultRWConcern": 1, "readConcern": {"atClusterTime": Timestamp(1, 1)}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="getDefaultRWConcern should reject atClusterTime without a snapshot level",
    ),
]

# Property [readConcern afterClusterTime Type Errors]: afterClusterTime is
# strictly typed as a timestamp, so every non-timestamp value is rejected.
GETDEFAULTRWCONCERN_READ_CONCERN_AFTER_CLUSTER_TIME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_after_cluster_time_type_{tid}",
        command={"getDefaultRWConcern": 1, "readConcern": {"afterClusterTime": val}},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getDefaultRWConcern should reject a {tid} afterClusterTime as a non-timestamp",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(2)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "x"),
        ("null", None),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("array", [1]),
        ("object", {"a": 1}),
    ]
]

# Property [readConcern afterClusterTime Value Errors]: a zero-valued (null)
# timestamp is a valid timestamp type but not a usable cluster time, so
# afterClusterTime rejects it.
GETDEFAULTRWCONCERN_READ_CONCERN_AFTER_CLUSTER_TIME_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_after_cluster_time_null_timestamp",
        command={"getDefaultRWConcern": 1, "readConcern": {"afterClusterTime": Timestamp(0, 0)}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="getDefaultRWConcern should reject a null timestamp afterClusterTime",
    ),
]

# Property [readConcern atClusterTime Type Errors]: atClusterTime is strictly
# typed as a timestamp, so every non-timestamp value is rejected.
GETDEFAULTRWCONCERN_READ_CONCERN_AT_CLUSTER_TIME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"read_concern_at_cluster_time_type_{tid}",
        command={"getDefaultRWConcern": 1, "readConcern": {"atClusterTime": val}},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getDefaultRWConcern should reject a {tid} atClusterTime as a non-timestamp",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(2)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "x"),
        ("null", None),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("array", [1]),
        ("object", {"a": 1}),
    ]
]

# Property [readConcern Sub-Field Validation]: an unknown sub-field inside the
# readConcern document is rejected.
GETDEFAULTRWCONCERN_READ_CONCERN_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "read_concern_unknown_subfield",
        command={"getDefaultRWConcern": 1, "readConcern": {"level": "local", "unknownField": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="getDefaultRWConcern should reject an unknown readConcern sub-field",
    ),
]

GETDEFAULTRWCONCERN_READ_CONCERN_ALL_TESTS: list[CommandTestCase] = (
    GETDEFAULTRWCONCERN_READ_CONCERN_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_TYPE_ERROR_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_LEVEL_TYPE_ERROR_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_LEVEL_VALUE_ERROR_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_ERROR_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_AT_CLUSTER_TIME_ERROR_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_AFTER_CLUSTER_TIME_TYPE_ERROR_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_AFTER_CLUSTER_TIME_VALUE_ERROR_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_AT_CLUSTER_TIME_TYPE_ERROR_TESTS
    + GETDEFAULTRWCONCERN_READ_CONCERN_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.requires(cluster_admin=True)
@pytest.mark.parametrize("test", pytest_params(GETDEFAULTRWCONCERN_READ_CONCERN_ALL_TESTS))
def test_getDefaultRWConcern_read_concern(collection, test):
    """Test getDefaultRWConcern readConcern acceptance and rejection behavior."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
