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
from bson.binary import UUID_SUBTYPE

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, NotExists
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [Null Field Handling]: a null optional field is accepted and treated
# as absent, so it is not echoed back.
GETDEFAULTRWCONCERN_NULL_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_in_memory",
        command={"getDefaultRWConcern": 1, "inMemory": None},
        expected={"ok": Eq(1.0), "inMemory": NotExists()},
        msg="getDefaultRWConcern should treat a null inMemory as field-absent and not echo it",
    ),
    CommandTestCase(
        "null_comment",
        command={"getDefaultRWConcern": 1, "comment": None},
        expected={"ok": Eq(1.0), "comment": NotExists()},
        msg="getDefaultRWConcern should accept a null comment and not echo it",
    ),
    CommandTestCase(
        "null_all",
        command={"getDefaultRWConcern": None, "inMemory": None, "comment": None},
        expected={"ok": Eq(1.0), "inMemory": NotExists(), "comment": NotExists()},
        msg="getDefaultRWConcern should accept null command value, inMemory, and comment together",
    ),
]

# Property [Command Value Behavior]: the command value is ignored and never
# type-validated, so any BSON value is accepted.
GETDEFAULTRWCONCERN_COMMAND_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"command_value_{tid}",
        command={"getDefaultRWConcern": val},
        expected={"ok": Eq(1.0)},
        msg=f"getDefaultRWConcern should ignore a {tid} command value and succeed",
    )
    for tid, val in [
        ("null", None),
        ("int32", 42),
        ("int64", Int64(2)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("string", "hello"),
        ("empty_string", ""),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("array_single", [1]),
        ("object", {"a": 1}),
    ]
]

# Property [inMemory Behavior]: inMemory is echoed back only when set true;
# false or omitted is accepted but not echoed.
GETDEFAULTRWCONCERN_IN_MEMORY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "in_memory_true",
        command={"getDefaultRWConcern": 1, "inMemory": True},
        expected={"ok": Eq(1.0), "inMemory": Eq(True)},
        msg="getDefaultRWConcern should accept inMemory true and echo it back as true",
    ),
    CommandTestCase(
        "in_memory_false",
        command={"getDefaultRWConcern": 1, "inMemory": False},
        expected={"ok": Eq(1.0), "inMemory": NotExists()},
        msg="getDefaultRWConcern should accept inMemory false and not echo it",
    ),
    CommandTestCase(
        "in_memory_omitted",
        command={"getDefaultRWConcern": 1},
        expected={"ok": Eq(1.0), "inMemory": NotExists()},
        msg="getDefaultRWConcern should default omitted inMemory to false and not echo it",
    ),
]

# Property [comment Behavior]: comment accepts any BSON value and is never
# echoed back.
GETDEFAULTRWCONCERN_COMMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command={"getDefaultRWConcern": 1, "comment": val},
        expected={"ok": Eq(1.0), "comment": NotExists()},
        msg=f"getDefaultRWConcern should accept a {tid} comment and not echo it",
    )
    for tid, val in [
        ("string", "hello"),
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
        ("array", [1, 2, 3]),
        ("object", {"a": 1}),
    ]
]

# Property [Generic Command Options (smoke)]: the command accepts the generic
# command options shared across commands.
GETDEFAULTRWCONCERN_GENERIC_OPTIONS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "generic_max_time_ms",
        command={"getDefaultRWConcern": 1, "maxTimeMS": 100},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should accept a maxTimeMS option",
    ),
    CommandTestCase(
        "generic_api_version",
        command={"getDefaultRWConcern": 1, "apiVersion": "1"},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should accept an apiVersion option",
    ),
    CommandTestCase(
        "generic_read_preference",
        command={"getDefaultRWConcern": 1, "$readPreference": {"mode": "secondary"}},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should accept a $readPreference option",
    ),
    CommandTestCase(
        "generic_lsid",
        command={"getDefaultRWConcern": 1, "lsid": {"id": Binary(b"\x01" * 16, UUID_SUBTYPE)}},
        expected={"ok": Eq(1.0)},
        msg="getDefaultRWConcern should accept an lsid session option",
    ),
]

# Property [inMemory Type Errors]: inMemory is strictly typed as bool, so every
# non-bool, non-null value is rejected.
GETDEFAULTRWCONCERN_IN_MEMORY_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"in_memory_type_{tid}",
        command={"getDefaultRWConcern": 1, "inMemory": val},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"getDefaultRWConcern should reject a {tid} inMemory value as a non-bool",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(2)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("string", "x"),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("array", [1]),
        ("object", {"a": 1}),
    ]
]

# Property [Syntax Validation Errors]: an unknown top-level command field is
# rejected.
GETDEFAULTRWCONCERN_SYNTAX_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field",
        command={"getDefaultRWConcern": 1, "unknownField": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="getDefaultRWConcern should reject an unknown command field",
    ),
]

GETDEFAULTRWCONCERN_COMMAND_OPTION_TESTS: list[CommandTestCase] = (
    GETDEFAULTRWCONCERN_NULL_FIELD_TESTS
    + GETDEFAULTRWCONCERN_COMMAND_VALUE_TESTS
    + GETDEFAULTRWCONCERN_IN_MEMORY_TESTS
    + GETDEFAULTRWCONCERN_COMMENT_TESTS
    + GETDEFAULTRWCONCERN_GENERIC_OPTIONS_TESTS
    + GETDEFAULTRWCONCERN_IN_MEMORY_TYPE_ERROR_TESTS
    + GETDEFAULTRWCONCERN_SYNTAX_ERROR_TESTS
)


@pytest.mark.requires(cluster_admin=True)
@pytest.mark.parametrize("test", pytest_params(GETDEFAULTRWCONCERN_COMMAND_OPTION_TESTS))
def test_getDefaultRWConcern_command_options(collection, test):
    """Test getDefaultRWConcern command value and option acceptance and rejection behavior."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
