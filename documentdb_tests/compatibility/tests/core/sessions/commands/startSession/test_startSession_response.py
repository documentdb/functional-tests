"""Tests for startSession response structure and session ID uniqueness."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType

# Property [Response Structure]: startSession returns id (document with UUID),
# timeoutMinutes (integer), and ok (1.0).
STARTSESSION_RESPONSE_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "response_has_id",
        command=lambda ctx: {"startSession": 1},
        expected={"id": IsType("object")},
        msg="startSession response should contain an id field of type object",
    ),
    CommandTestCase(
        "response_id_has_uuid",
        command=lambda ctx: {"startSession": 1},
        expected={"id": {"id": IsType("binData")}},
        msg="startSession response id should contain an id sub-field of type binData",
    ),
    CommandTestCase(
        "response_has_timeout_minutes",
        command=lambda ctx: {"startSession": 1},
        expected={"timeoutMinutes": IsType("int")},
        msg="startSession response should contain timeoutMinutes of type int",
    ),
    CommandTestCase(
        "response_timeout_minutes_value",
        command=lambda ctx: {"startSession": 1},
        expected={"timeoutMinutes": Eq(30)},
        msg="startSession response timeoutMinutes should be 30",
    ),
    CommandTestCase(
        "response_has_ok",
        command=lambda ctx: {"startSession": 1},
        expected={"ok": Eq(1.0)},
        msg="startSession response should contain ok with value 1.0",
    ),
    CommandTestCase(
        "response_has_expected_keys",
        command=lambda ctx: {"startSession": 1},
        expected={"id": Exists(), "timeoutMinutes": Exists(), "ok": Exists()},
        msg="startSession response should contain id, timeoutMinutes, and ok",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_RESPONSE_STRUCTURE_TESTS))
def test_startSession_response_structure(database_client, collection, test):
    """Test startSession response structure properties."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )
    if isinstance(result, dict) and "id" in result:
        collection.database.command({"endSessions": [result["id"]]})


# Property [Session ID Uniqueness]: each startSession call returns a different UUID.
def test_startSession_unique_ids(collection):
    """Test startSession returns unique session IDs."""
    results = [execute_command(collection, {"startSession": 1}) for _ in range(5)]
    ids = [r["id"]["id"] for r in results]
    unique_count = len(set(ids))
    assertSuccessPartial(
        {"unique": unique_count, "total": len(ids)},
        {"unique": 5, "total": 5},
        msg="startSession should return 5 unique session IDs across 5 calls",
    )
    session_ids = [r["id"] for r in results if isinstance(r, dict) and "id" in r]
    if session_ids:
        collection.database.command({"endSessions": session_ids})
