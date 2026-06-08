"""Tests for getMore session behavior."""

from __future__ import annotations

from documentdb_tests.compatibility.tests.core.cursors.commands.utils.cursor_test_case import (
    open_find_cursors,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import CURSOR_SESSION_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Eq


# Property [Session Mismatch - Different Explicit Session]: getMore with a
# different explicit session than the cursor's produces
# CURSOR_SESSION_MISMATCH_ERROR.
def test_getMore_session_mismatch_different_session(collection):
    """Test getMore with a different explicit session produces session mismatch error."""
    collection.insert_many([{"_id": i} for i in range(10)])
    client = collection.database.client
    session_a = client.start_session()
    session_b = client.start_session()
    try:
        find_result = execute_command(
            collection, {"find": collection.name, "batchSize": 2}, session=session_a
        )
        cursor_id = find_result["cursor"]["id"]
        result = execute_command(
            collection,
            {"getMore": cursor_id, "collection": collection.name},
            session=session_b,
        )
        assertResult(
            result,
            error_code=CURSOR_SESSION_MISMATCH_ERROR,
            msg="getMore should reject a different explicit session than the cursor's",
            raw_res=True,
        )
    finally:
        session_a.end_session()
        session_b.end_session()


# Property [Session Match - Same Session]: getMore with the same explicit
# session as the cursor succeeds.
def test_getMore_session_same_session_succeeds(collection):
    """Test getMore with the same explicit session succeeds."""
    collection.insert_many([{"_id": i} for i in range(10)])
    client = collection.database.client
    session_a = client.start_session()
    try:
        find_result = execute_command(
            collection, {"find": collection.name, "batchSize": 2}, session=session_a
        )
        cursor_id = find_result["cursor"]["id"]
        result = execute_command(
            collection,
            {"getMore": cursor_id, "collection": collection.name},
            session=session_a,
        )
        assertResult(
            result,
            expected={"ok": Eq(1.0)},
            msg="getMore should succeed with the same explicit session",
            raw_res=True,
        )
    finally:
        session_a.end_session()


# Property [Session - Implicit Cursor, Explicit getMore]: getMore with an
# explicit session on an implicit-session cursor succeeds.
def test_getMore_session_implicit_cursor_explicit_getmore(collection):
    """Test getMore with explicit session on implicit session cursor succeeds."""
    collection.insert_many([{"_id": i} for i in range(10)])
    client = collection.database.client
    (cursor_id,) = open_find_cursors(collection, 1, batch_size=2)
    session_b = client.start_session()
    try:
        result = execute_command(
            collection,
            {"getMore": cursor_id, "collection": collection.name},
            session=session_b,
        )
        assertResult(
            result,
            expected={"ok": Eq(1.0)},
            msg="getMore should succeed with explicit session on implicit session cursor",
            raw_res=True,
        )
    finally:
        session_b.end_session()


# Property [Session - Explicit Cursor, Implicit getMore]: getMore without an
# explicit session on an explicit-session cursor produces
# CURSOR_SESSION_MISMATCH_ERROR.
def test_getMore_session_explicit_cursor_implicit_getmore(collection):
    """Test getMore without explicit session on explicit session cursor produces error."""
    collection.insert_many([{"_id": i} for i in range(10)])
    client = collection.database.client
    session_a = client.start_session()
    try:
        find_result = execute_command(
            collection, {"find": collection.name, "batchSize": 2}, session=session_a
        )
        cursor_id = find_result["cursor"]["id"]
        result = execute_command(
            collection,
            {"getMore": cursor_id, "collection": collection.name},
        )
        assertResult(
            result,
            error_code=CURSOR_SESSION_MISMATCH_ERROR,
            msg=(
                "getMore should reject implicit session when cursor was"
                " created with explicit session"
            ),
            raw_res=True,
        )
    finally:
        session_a.end_session()


# Property [Session Survives End]: getMore succeeds after the originating
# session has ended.
def test_getMore_session_survives_session_end(collection):
    """Test getMore succeeds after the originating session has ended."""
    collection.insert_many([{"_id": i} for i in range(10)])
    client = collection.database.client
    session_a = client.start_session()
    find_result = execute_command(
        collection, {"find": collection.name, "batchSize": 2}, session=session_a
    )
    cursor_id = find_result["cursor"]["id"]
    session_a.end_session()
    result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0)},
        msg="getMore should succeed after the originating session has ended",
        raw_res=True,
    )
