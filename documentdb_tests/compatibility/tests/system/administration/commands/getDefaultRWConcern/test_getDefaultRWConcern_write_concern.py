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
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [writeConcern Acceptance]: a null writeConcern is treated as absent
# and accepted.
GETDEFAULTRWCONCERN_WRITE_CONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "write_concern_null",
        command={"getDefaultRWConcern": 1, "writeConcern": None},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should treat a null writeConcern as field-absent and succeed",
    ),
]

# Property [Unsupported writeConcern]: writeConcern is not supported, so any
# writeConcern object is rejected.
GETDEFAULTRWCONCERN_WRITE_CONCERN_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "write_concern_non_empty",
        command={"getDefaultRWConcern": 1, "writeConcern": {"w": "majority"}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="getDefaultRWConcern should reject a non-empty writeConcern object as unsupported",
    ),
    CommandTestCase(
        "write_concern_empty",
        command={"getDefaultRWConcern": 1, "writeConcern": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="getDefaultRWConcern should reject an empty writeConcern object as unsupported",
    ),
]

# Property [writeConcern Type Errors]: a non-object writeConcern is rejected by
# the object type check.
GETDEFAULTRWCONCERN_WRITE_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"write_concern_type_{tid}",
        command={"getDefaultRWConcern": 1, "writeConcern": val},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getDefaultRWConcern should reject a {tid} writeConcern as a non-object",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(2)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "majority"),
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

GETDEFAULTRWCONCERN_WRITE_CONCERN_ALL_TESTS: list[CommandTestCase] = (
    GETDEFAULTRWCONCERN_WRITE_CONCERN_TESTS
    + GETDEFAULTRWCONCERN_WRITE_CONCERN_ERROR_TESTS
    + GETDEFAULTRWCONCERN_WRITE_CONCERN_TYPE_ERROR_TESTS
)


@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(GETDEFAULTRWCONCERN_WRITE_CONCERN_ALL_TESTS))
def test_getDefaultRWConcern_write_concern(collection, test):
    """Test getDefaultRWConcern writeConcern acceptance and rejection behavior."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
