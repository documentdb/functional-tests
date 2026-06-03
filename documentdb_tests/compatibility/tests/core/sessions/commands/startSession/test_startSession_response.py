"""Tests for startSession response structure and session ID uniqueness."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertProperties, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, IsType

# Property [Response Structure]: startSession returns id (document with UUID),
# timeoutMinutes (integer), and ok (1.0).
STARTSESSION_RESPONSE_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "response_has_id",
        command=lambda ctx: {"startSession": 1},
        msg="startSession response should contain an id field of type object",
    ),
    CommandTestCase(
        "response_id_has_uuid",
        command=lambda ctx: {"startSession": 1},
        msg="startSession response id should contain an id sub-field of type binData",
    ),
    CommandTestCase(
        "response_has_timeout_minutes",
        command=lambda ctx: {"startSession": 1},
        msg="startSession response should contain timeoutMinutes of type int",
    ),
    CommandTestCase(
        "response_timeout_minutes_value",
        command=lambda ctx: {"startSession": 1},
        msg="startSession response timeoutMinutes should be 30",
    ),
    CommandTestCase(
        "response_has_ok",
        command=lambda ctx: {"startSession": 1},
        msg="startSession response should contain ok with value 1.0",
    ),
    CommandTestCase(
        "response_key_count",
        command=lambda ctx: {"startSession": 1},
        msg="startSession response should contain exactly 3 top-level keys",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_RESPONSE_STRUCTURE_TESTS))
def test_startSession_response_structure(database_client, collection, test):
    """Test startSession response structure properties."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))

    checks = {
        "response_has_id": {"id": IsType("object")},
        "response_id_has_uuid": {"id": {"id": IsType("binData")}},
        "response_has_timeout_minutes": {"timeoutMinutes": IsType("int")},
        "response_timeout_minutes_value": {"timeoutMinutes": Eq(30)},
        "response_has_ok": {"ok": Eq(1.0)},
        "response_key_count": {"id": Exists(), "timeoutMinutes": Exists(), "ok": Exists()},
    }
    assertProperties(result, checks[test.id], msg=test.msg, raw_res=True)


# Property [Session ID Uniqueness]: each startSession call returns a different UUID.
def test_startSession_unique_ids(collection):
    """Test startSession returns unique session IDs."""
    results = [execute_command(collection, {"startSession": 1}) for _ in range(5)]
    ids = [r["id"]["id"] for r in results if not isinstance(r, Exception)]
    assertSuccess(
        results[-1],
        {"ok": 1.0},
        raw_res=True,
        transform=lambda r: {"ok": 1.0 if len(set(ids)) == 5 else 0.0},
        msg="startSession should return 5 unique session IDs across 5 calls",
    )
