"""Tests for killSessions core behavior and comment acceptance."""

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import CURSOR_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Random UUID]: killSessions with a non-matching UUID succeeds
# silently without error.
KILLSESSIONS_RANDOM_UUID_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "random_uuid_single",
        command=lambda ctx: {"killSessions": [{"id": Binary(uuid.uuid4().bytes, 4)}]},
        expected={"ok": 1.0},
        msg="killSessions should succeed with a random non-matching UUID",
    ),
    CommandTestCase(
        "random_uuid_two",
        command=lambda ctx: {
            "killSessions": [
                {"id": Binary(uuid.uuid4().bytes, 4)},
                {"id": Binary(uuid.uuid4().bytes, 4)},
            ]
        },
        expected={"ok": 1.0},
        msg="killSessions should succeed with two random UUIDs",
    ),
    CommandTestCase(
        "random_uuid_five",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(uuid.uuid4().bytes, 4)} for _ in range(5)]
        },
        expected={"ok": 1.0},
        msg="killSessions should succeed with five random UUIDs",
    ),
]

# Property [Duplicate UUIDs]: duplicate session IDs in the array are
# accepted without error.
KILLSESSIONS_DUPLICATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "duplicate_uuids",
        command=lambda ctx: {
            "killSessions": [
                {"id": Binary(b"\xde\xad" * 8, subtype=4)},
                {"id": Binary(b"\xde\xad" * 8, subtype=4)},
            ]
        },
        expected={"ok": 1.0},
        msg="killSessions should accept duplicate UUIDs without error",
    ),
]

# Property [Large Array]: killSessions handles a large array of session
# identifiers without error.
KILLSESSIONS_LARGE_ARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "large_array_100",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(uuid.uuid4().bytes, 4)} for _ in range(100)]
        },
        expected={"ok": 1.0},
        msg="killSessions should handle 100 session identifiers",
    ),
]

# Property [comment Field Universal Type Acceptance]: all BSON types
# representable by pymongo are accepted for the comment field without
# restriction.
KILLSESSIONS_COMMENT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command=lambda ctx, v=val: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "comment": v,
        },
        expected={"ok": 1.0},
        msg=f"killSessions should accept {tid} comment",
    )
    for tid, val in [
        ("string", "test comment"),
        ("string_empty", ""),
        ("int32", 42),
        ("int64", Int64(123)),
        ("double", 3.14),
        ("decimal128", Decimal128("1.5")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("object", {"key": "value"}),
        ("object_empty", {}),
        ("array", [1, "two", 3.0]),
        ("array_empty", []),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Database Context]: killSessions succeeds when run on
# the admin database (not just the default test database).
KILLSESSIONS_ADMIN_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "admin_database",
        command=lambda ctx: {"killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}]},
        expected={"ok": 1.0},
        msg="killSessions should succeed on admin database",
    ),
]

KILLSESSIONS_CORE_TESTS: list[CommandTestCase] = (
    KILLSESSIONS_RANDOM_UUID_TESTS
    + KILLSESSIONS_DUPLICATE_TESTS
    + KILLSESSIONS_LARGE_ARRAY_TESTS
    + KILLSESSIONS_COMMENT_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_CORE_TESTS))
def test_killSessions_core(collection, test):
    """Test killSessions core behavior."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_ADMIN_DB_TESTS))
def test_killSessions_admin_db(collection, test):
    """Test killSessions on admin database."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.no_parallel
def test_killSessions_real_session(collection):
    """Test killSessions kills a real active session.

    Opens a cursor under the session, kills the session, then verifies
    that getMore fails with CursorNotFound — proving the kill closed
    the cursor.
    """
    client = collection.database.client
    db = collection.database
    session = client.start_session()
    lsid = session.session_id["id"]

    # Insert enough docs to require a getMore.
    collection.insert_many([{"_id": i} for i in range(10)], session=session)

    # Open a cursor with a small batch so the first batch doesn't exhaust it.
    find_result = db.command(
        {"find": collection.name, "batchSize": 2},
        session=session,
    )
    cursor_id = find_result["cursor"]["id"]

    # Kill the session.
    execute_command(collection, {"killSessions": [{"id": lsid}]})

    # getMore on the killed session's cursor should fail with CursorNotFound,
    # proving the kill closed the cursor.
    get_more_result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
        session=session,
    )
    assertResult(
        get_more_result,
        error_code=CURSOR_NOT_FOUND_ERROR,
        msg="getMore should fail after session is killed",
        raw_res=True,
    )
