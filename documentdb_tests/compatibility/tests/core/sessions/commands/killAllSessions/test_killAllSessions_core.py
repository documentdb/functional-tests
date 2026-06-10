"""Tests for killAllSessions core behavior, user array formats, and unrecognized fields."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel

# Property [Test Database]: killAllSessions succeeds on the test database.
KILLALLSESSIONS_TEST_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "test_database",
        command=lambda ctx: {"killAllSessions": []},
        expected={"ok": 1.0},
        msg="killAllSessions should succeed on the test database",
    ),
]

# Property [Response OK]: killAllSessions returns ok field with value 1.0.
KILLALLSESSIONS_RESPONSE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "response_ok",
        command=lambda ctx: {"killAllSessions": []},
        expected={"ok": 1.0},
        msg="killAllSessions should return ok: 1.0",
    ),
]

# Property [Empty Array]: killAllSessions with an empty array kills all sessions.
# Property [Single User Entry]: killAllSessions with a single {user, db} entry succeeds.
# Property [Multiple User Entries]: killAllSessions with multiple entries succeeds.
# Property [Non-Existent User]: killAllSessions with a non-existent user succeeds silently.
# Property [Duplicate User Entries]: killAllSessions with duplicate entries succeeds.
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

# Property [Null Array Element Acceptance]: null elements in the user array
# are silently accepted without error.
# Property [Empty String User/DB]: killAllSessions with empty string user or db values.
# Property [Unicode User/DB Names]: killAllSessions with unicode characters.
# Property [Special Characters in Names]: killAllSessions with special characters.
# Property [Large User Array]: killAllSessions with many user entries succeeds.
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

# Property [Idempotent Behavior]: calling killAllSessions multiple times succeeds.
KILLALLSESSIONS_IDEMPOTENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "idempotent",
        command=lambda ctx: {"killAllSessions": []},
        expected={"ok": 1.0},
        msg="killAllSessions should succeed on repeated calls",
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
    CommandTestCase(
        "unrecognized_case_variant",
        command=lambda ctx: {"killAllSessions": [], "KillAllSessions": 1},
        expected={"ok": 1.0},
        msg="killAllSessions should ignore case-variant of command name",
    ),
]

KILLALLSESSIONS_CORE_TESTS: list[CommandTestCase] = (
    KILLALLSESSIONS_TEST_DB_TESTS
    + KILLALLSESSIONS_RESPONSE_TESTS
    + KILLALLSESSIONS_USER_ARRAY_TESTS
    + KILLALLSESSIONS_EDGE_CASE_TESTS
    + KILLALLSESSIONS_IDEMPOTENT_TESTS
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


def test_killAllSessions_admin_database(collection):
    """Test killAllSessions succeeds on the admin database."""
    result = execute_admin_command(collection, {"killAllSessions": []})
    assertResult(
        result,
        expected={"ok": 1.0},
        msg="killAllSessions should succeed on the admin database",
        raw_res=True,
    )


def test_killAllSessions_kill_after_start(collection):
    """Test killAllSessions after starting a session succeeds."""
    execute_command(collection, {"startSession": 1})
    result = execute_command(collection, {"killAllSessions": []})
    assertResult(
        result,
        expected={"ok": 1.0},
        msg="killAllSessions after startSession should succeed",
        raw_res=True,
    )
