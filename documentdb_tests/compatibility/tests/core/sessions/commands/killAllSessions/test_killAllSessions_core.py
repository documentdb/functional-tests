"""Tests for killAllSessions core behavior, user array formats, and unrecognized fields."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import CURSOR_NOT_FOUND_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# killAllSessions kills sessions server-wide, so these tests must never run in
# parallel with other tests that rely on open sessions or cursors.
pytestmark = pytest.mark.no_parallel

# Property [User Array Formats]: killAllSessions accepts various user array
# formats including empty, single, multiple, non-existent, and duplicate entries.
KILLALLSESSIONS_USER_ARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_array",
        command=lambda ctx: {"killAllSessions": []},
        expected={"ok": 1.0},
        msg="killAllSessions with empty array should succeed",
    ),
    CommandTestCase(
        "single_user_entry",
        command=lambda ctx: {
            "killAllSessions": [{"user": "testUser", "db": "admin"}],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with single user entry should succeed",
    ),
    CommandTestCase(
        "multiple_user_entries",
        command=lambda ctx: {
            "killAllSessions": [
                {"user": "user1", "db": "db1"},
                {"user": "user2", "db": "db2"},
            ],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with multiple user entries should succeed",
    ),
    CommandTestCase(
        "non_existent_user",
        command=lambda ctx: {
            "killAllSessions": [{"user": "doesNotExist", "db": "nonExistentDb"}],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with non-existent user should succeed silently",
    ),
    CommandTestCase(
        "duplicate_user_entries",
        command=lambda ctx: {
            "killAllSessions": [
                {"user": "test", "db": "admin"},
                {"user": "test", "db": "admin"},
            ],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with duplicate user entries should succeed",
    ),
]

# Property [Edge Cases]: killAllSessions handles edge cases including null
# entries, empty strings, unicode, special characters, and large arrays.
KILLALLSESSIONS_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_array_entry",
        command=lambda ctx: {"killAllSessions": [None]},
        expected={"ok": 1.0},
        msg="killAllSessions should accept null array entry",
    ),
    CommandTestCase(
        "empty_string_user",
        command=lambda ctx: {
            "killAllSessions": [{"user": "", "db": "admin"}],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with empty string user should succeed",
    ),
    CommandTestCase(
        "empty_string_db",
        command=lambda ctx: {
            "killAllSessions": [{"user": "test", "db": ""}],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with empty string db should succeed",
    ),
    CommandTestCase(
        "empty_string_both",
        command=lambda ctx: {
            "killAllSessions": [{"user": "", "db": ""}],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with empty string user and db should succeed",
    ),
    CommandTestCase(
        "unicode_user",
        command=lambda ctx: {
            "killAllSessions": [{"user": "\u00e9", "db": "admin"}],  # precomposed e-acute
        },
        expected={"ok": 1.0},
        msg="killAllSessions with unicode user should succeed",
    ),
    CommandTestCase(
        "unicode_db",
        command=lambda ctx: {
            "killAllSessions": [{"user": "test", "db": "\u00e9"}],  # precomposed e-acute
        },
        expected={"ok": 1.0},
        msg="killAllSessions with unicode db should succeed",
    ),
    CommandTestCase(
        "special_chars_dots",
        command=lambda ctx: {
            "killAllSessions": [{"user": "user.with.dots", "db": "admin"}],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with dots in user should succeed",
    ),
    CommandTestCase(
        "special_chars_dollar",
        command=lambda ctx: {
            "killAllSessions": [{"user": "user$dollar", "db": "admin"}],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with dollar sign in user should succeed",
    ),
    CommandTestCase(
        "large_user_array",
        command=lambda ctx: {
            "killAllSessions": [{"user": f"user{i}", "db": f"db{i}"} for i in range(20)],
        },
        expected={"ok": 1.0},
        msg="killAllSessions with 20 user entries should succeed",
    ),
]

# Property [Unrecognized Field Acceptance]: unknown fields are silently ignored.
KILLALLSESSIONS_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_single",
        command=lambda ctx: {"killAllSessions": [], "unknownField": 1},
        expected={"ok": 1.0},
        msg="killAllSessions should ignore a single unknown field",
    ),
    CommandTestCase(
        "unrecognized_multiple",
        command=lambda ctx: {"killAllSessions": [], "foo": 1, "bar": 2},
        expected={"ok": 1.0},
        msg="killAllSessions should ignore multiple unknown fields",
    ),
    CommandTestCase(
        "unrecognized_dollar_prefix",
        command=lambda ctx: {"killAllSessions": [], "$unknown": 1},
        expected={"ok": 1.0},
        msg="killAllSessions should ignore dollar-prefixed unknown field",
    ),
    CommandTestCase(
        "unrecognized_other_command",
        command=lambda ctx: {"killAllSessions": [], "query": {"x": 1}},
        expected={"ok": 1.0},
        msg="killAllSessions should ignore field from another command",
    ),
]

KILLALLSESSIONS_CORE_TESTS: list[CommandTestCase] = (
    KILLALLSESSIONS_USER_ARRAY_TESTS
    + KILLALLSESSIONS_EDGE_CASE_TESTS
    + KILLALLSESSIONS_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLALLSESSIONS_CORE_TESTS))
def test_killAllSessions_core(collection, test):
    """Test killAllSessions core behavior."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Admin Database]: killAllSessions succeeds on the admin database.
def test_killAllSessions_admin_database(collection):
    """Test killAllSessions succeeds on the admin database."""
    result = execute_admin_command(collection, {"killAllSessions": []})
    assertResult(
        result,
        expected={"ok": 1.0},
        msg="killAllSessions should succeed on the admin database",
        raw_res=True,
    )


# Property [Idempotent Behavior]: calling killAllSessions multiple times succeeds.
def test_killAllSessions_idempotent(collection):
    """Test killAllSessions succeeds on repeated calls."""
    execute_command(collection, {"killAllSessions": []})
    result = execute_command(collection, {"killAllSessions": []})
    assertResult(
        result,
        expected={"ok": 1.0},
        msg="killAllSessions should succeed on second call",
        raw_res=True,
    )


# Property [Kill After Start]: killAllSessions kills an active session.
def test_killAllSessions_kill_after_start(collection):
    """Test killAllSessions kills an active session.

    Opens a cursor under a session, kills all sessions, then verifies
    that getMore fails with CursorNotFound — proving the kill closed
    the cursor.
    """
    client = collection.database.client
    db = collection.database
    session = client.start_session()
    try:
        # Insert enough docs to require a getMore.
        collection.insert_many([{"_id": i} for i in range(10)], session=session)

        # Open a cursor with a small batch so the first batch doesn't exhaust it.
        find_result = db.command(
            {"find": collection.name, "batchSize": 2},
            session=session,
        )
        cursor_id = find_result["cursor"]["id"]

        # Kill all sessions.
        execute_command(collection, {"killAllSessions": []})

        # getMore on the killed session's cursor should fail.
        get_more_result = execute_command(
            collection,
            {"getMore": cursor_id, "collection": collection.name},
            session=session,
        )
        assertResult(
            get_more_result,
            error_code=CURSOR_NOT_FOUND_ERROR,
            msg="getMore should fail after killAllSessions",
            raw_res=True,
        )
    finally:
        session.end_session()


# Property [Targeted Filter]: killAllSessions with a {user, db} filter only
# kills sessions belonging to the matched user; unrelated cursors survive.
def test_killAllSessions_targeted_filter(collection):
    """Test killAllSessions honours the {user, db} filter.

    Opens a cursor under a session, then calls killAllSessions with a
    non-matching {user, db} filter.  The cursor should survive because the
    filter does not match the current connection's user.  This proves the
    filter is evaluated rather than ignored.
    """
    client = collection.database.client
    db = collection.database
    session = client.start_session()
    try:
        # Insert enough docs to require a getMore.
        collection.insert_many([{"_id": i} for i in range(10)], session=session)

        # Open a cursor with a small batch so the first batch doesn't exhaust it.
        find_result = db.command(
            {"find": collection.name, "batchSize": 2},
            session=session,
        )
        cursor_id = find_result["cursor"]["id"]

        # Kill sessions for a non-existent user — should NOT affect our cursor.
        execute_command(
            collection,
            {"killAllSessions": [{"user": "nonExistentUser", "db": "nonExistentDb"}]},
        )

        # getMore should still succeed because the filter did not match.
        get_more_result = execute_command(
            collection,
            {"getMore": cursor_id, "collection": collection.name},
            session=session,
        )
        assertResult(
            get_more_result,
            expected={"ok": Eq(1.0)},
            msg="getMore should succeed after killAllSessions with non-matching filter",
            raw_res=True,
        )
    finally:
        session.end_session()
