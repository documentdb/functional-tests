"""Tests for killSessions core behavior and response structure."""

from __future__ import annotations

import uuid

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel


# Property [Empty Array]: killSessions with an empty array succeeds.
KILLSESSIONS_EMPTY_ARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_array",
        command=lambda ctx: {"killSessions": []},
        expected={"ok": 1.0},
        msg="killSessions should succeed with empty array",
    ),
]

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
                {"id": Binary(b"\x00" * 16, subtype=4)},
                {"id": Binary(b"\x00" * 16, subtype=4)},
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

KILLSESSIONS_CORE_TESTS: list[CommandTestCase] = (
    KILLSESSIONS_EMPTY_ARRAY_TESTS
    + KILLSESSIONS_RANDOM_UUID_TESTS
    + KILLSESSIONS_DUPLICATE_TESTS
    + KILLSESSIONS_LARGE_ARRAY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_CORE_TESTS))
def test_killSessions_core(collection, test):
    """Test killSessions core behavior."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
