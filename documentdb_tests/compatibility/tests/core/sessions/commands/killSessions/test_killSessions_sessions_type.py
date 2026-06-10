"""Tests for killSessions array element and session ID type validation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_UUID_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


def _random_uuid() -> Binary:
    """Generate a random UUID as Binary subtype 4."""
    return Binary(uuid.uuid4().bytes, subtype=4)


# Property [Non-Document Array Elements]: array elements that are not
# documents are rejected (except null, which is silently accepted).
KILLSESSIONS_ELEMENT_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"element_type_{tid}",
        command=lambda ctx, v=val: {"killSessions": [v]},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killSessions should reject {tid} array element",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("string", "string"),
        ("bool_true", True),
        ("array", []),
        ("binary", Binary(b"\x00")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Null Array Element Acceptance]: null elements in the array
# are silently accepted without error.
KILLSESSIONS_NULL_ELEMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "element_null_accepted",
        command=lambda ctx: {"killSessions": [None]},
        expected={"ok": 1.0},
        msg="killSessions should accept null array element",
    ),
    CommandTestCase(
        "element_null_after_valid",
        command=lambda ctx: {"killSessions": [{"id": _random_uuid()}, None]},
        expected={"ok": 1.0},
        msg="killSessions should accept null element after valid element",
    ),
]

# Property [Invalid Document Elements]: documents missing the required
# id field or containing wrong field names are rejected.
KILLSESSIONS_INVALID_DOC_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "element_empty_doc",
        command=lambda ctx: {"killSessions": [{}]},
        error_code=MISSING_FIELD_ERROR,
        msg="killSessions should reject empty document element",
    ),
    CommandTestCase(
        "element_wrong_field",
        command=lambda ctx: {"killSessions": [{"notId": _random_uuid()}]},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killSessions should reject document with wrong field name",
    ),
    CommandTestCase(
        "element_unrelated_fields",
        command=lambda ctx: {"killSessions": [{"foo": "bar"}]},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killSessions should reject document with unrelated fields",
    ),
]

# Property [Mixed Valid and Invalid Elements]: an invalid element after
# a valid one is still rejected.
KILLSESSIONS_MIXED_ELEMENT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "mixed_valid_then_int",
        command=lambda ctx: {"killSessions": [{"id": _random_uuid()}, 1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="killSessions should reject int element after valid element",
    ),
]

# Property [Session ID Type Rejection]: the id field must be a UUID
# (Binary subtype 4). All other types are rejected.
KILLSESSIONS_ID_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"id_type_{tid}",
        command=lambda ctx, v=val: {"killSessions": [{"id": v}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killSessions should reject {tid} as session id",
    )
    for tid, val in [
        ("string", "not-a-uuid-string"),
        ("int32", 12345),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", []),
        ("object", {}),
        ("objectid", ObjectId()),
        ("binary_subtype0", Binary(b"\x00" * 16, subtype=0)),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
] + [
    # Null id produces a missing field error rather than a type mismatch.
    CommandTestCase(
        "id_type_null",
        command=lambda ctx: {"killSessions": [{"id": None}]},
        error_code=MISSING_FIELD_ERROR,
        msg="killSessions should reject null as session id",
    ),
]

# Property [UUID Binary Size Rejection]: Binary subtype 4 values that are
# not exactly 16 bytes are rejected with INVALID_UUID_ERROR.
KILLSESSIONS_UUID_SIZE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "uuid_too_short",
        command=lambda ctx: {"killSessions": [{"id": Binary(b"\x00" * 8, subtype=4)}]},
        error_code=INVALID_UUID_ERROR,
        msg="killSessions should reject Binary subtype 4 with 8 bytes",
    ),
    CommandTestCase(
        "uuid_too_long",
        command=lambda ctx: {"killSessions": [{"id": Binary(b"\x00" * 32, subtype=4)}]},
        error_code=INVALID_UUID_ERROR,
        msg="killSessions should reject Binary subtype 4 with 32 bytes",
    ),
]

# Property [Extra Fields in Session Identifier]: documents with extra
# fields alongside id are rejected.
KILLSESSIONS_EXTRA_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "extra_field_alongside_id",
        command=lambda ctx: {"killSessions": [{"id": _random_uuid(), "extra": 1}]},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killSessions should reject extra fields alongside id",
    ),
]

# Property [Valid UUID]: a standard UUID (Binary subtype 4, 16 bytes) is
# accepted as a session id.
KILLSESSIONS_VALID_UUID_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "valid_uuid",
        command=lambda ctx: {"killSessions": [{"id": _random_uuid()}]},
        expected={"ok": 1.0},
        msg="killSessions should accept a valid UUID session id",
    ),
]

# Property [Binary Subtype 3]: Binary subtype 3 (old UUID) is rejected
# for the id field.
KILLSESSIONS_BINARY_SUBTYPE3_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "id_binary_subtype3",
        command=lambda ctx: {"killSessions": [{"id": Binary(b"\x00" * 16, subtype=3)}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="killSessions should reject Binary subtype 3 as session id",
    ),
]

KILLSESSIONS_SESSIONS_TYPE_TESTS: list[CommandTestCase] = (
    KILLSESSIONS_ELEMENT_TYPE_ERROR_TESTS
    + KILLSESSIONS_NULL_ELEMENT_TESTS
    + KILLSESSIONS_INVALID_DOC_ERROR_TESTS
    + KILLSESSIONS_MIXED_ELEMENT_ERROR_TESTS
    + KILLSESSIONS_ID_TYPE_ERROR_TESTS
    + KILLSESSIONS_UUID_SIZE_ERROR_TESTS
    + KILLSESSIONS_EXTRA_FIELDS_TESTS
    + KILLSESSIONS_VALID_UUID_TESTS
    + KILLSESSIONS_BINARY_SUBTYPE3_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_SESSIONS_TYPE_TESTS))
def test_killSessions_sessions_type(collection, test):
    """Test killSessions array element and session ID type validation."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
