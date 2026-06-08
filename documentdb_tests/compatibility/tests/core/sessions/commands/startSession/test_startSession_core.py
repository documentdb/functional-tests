"""Tests for startSession database-agnostic behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Test Database]: startSession succeeds on the test database.
STARTSESSION_TEST_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "test_db",
        command=lambda ctx: {"startSession": 1},
        expected={"ok": Eq(1.0)},
        msg="startSession should succeed on the test database",
    ),
]

# Property [Admin Database]: startSession succeeds on the admin database.
STARTSESSION_ADMIN_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "admin_db",
        command=lambda ctx: {"startSession": 1},
        expected={"ok": Eq(1.0)},
        msg="startSession should succeed on the admin database",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_TEST_DB_TESTS))
def test_startSession_on_test_database(database_client, collection, test):
    """Test startSession on the test database."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_ADMIN_DB_TESTS))
def test_startSession_on_admin_database(database_client, collection, test):
    """Test startSession on the admin database."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )
