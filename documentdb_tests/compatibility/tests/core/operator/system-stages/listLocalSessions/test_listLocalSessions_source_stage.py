"""Tests for $listLocalSessions source-stage behavior: output shape and database independence."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import (
    ByteLen,
    Eq,
    IsType,
)


# Property [Return Type / Output Shape]: each session document is {_id: {id, uid}, lastUse},
# where id is the session's UUID, uid is a 32-byte digest of the authenticated user, and
# lastUse is a date.
@pytest.mark.aggregate
def test_listLocalSessions_output_shape(collection: Collection):
    """Test $listLocalSessions session document shape."""
    # Match the opened session's id so we validate the document we control.
    with collection.database.client.start_session() as session:
        collection.database.command("ping", session=session)
        session_id = session.session_id["id"]
        result = execute_command(
            collection,
            {
                "aggregate": 1,
                "pipeline": [
                    {"$listLocalSessions": {}},
                    {"$match": {"_id.id": session_id}},
                ],
                "cursor": {},
            },
            session=session,
        )
    assertResult(
        result,
        expected={
            "_id": {
                "id": Eq(session_id),
                "uid": ByteLen(32),
            },
            "lastUse": IsType("date"),
        },
        msg="$listLocalSessions returns the opened session shaped as {_id: {id, uid}, lastUse}",
    )


# Property [uid Identifies the User]: uid is a digest of the authenticated user, not the
# session, so two distinct sessions of the same user share one uid while their ids differ.
# Grouping both sessions by uid therefore yields a single group holding both session ids.
@pytest.mark.aggregate
def test_listLocalSessions_uid_is_per_user(collection: Collection):
    """Test two sessions of one user group under a single shared uid."""
    client = collection.database.client
    with client.start_session() as first, client.start_session() as second:
        collection.database.command("ping", session=first)
        collection.database.command("ping", session=second)
        first_id = first.session_id["id"]
        second_id = second.session_id["id"]
        result = execute_command(
            collection,
            {
                "aggregate": 1,
                "pipeline": [
                    {"$listLocalSessions": {}},
                    {"$match": {"_id.id": {"$in": [first_id, second_id]}}},
                    {"$group": {"_id": "$_id.uid", "sessionIds": {"$addToSet": "$_id.id"}}},
                    {"$project": {"_id": 0, "numSessions": {"$size": "$sessionIds"}}},
                ],
                "cursor": {},
            },
            session=first,
        )
    assertResult(
        result,
        expected=[{"numSessions": 2}],
        msg="two sessions of one user should group under a single shared uid",
    )


# Property [Database Independence]: $listLocalSessions is instance-local, so it succeeds
# regardless of which database the aggregate command targets. Cover both an admin and a
# non-admin database, since a system stage could plausibly be gated to the admin database;
# the target database is otherwise immaterial because the stage reads instance-local state.
@pytest.mark.aggregate
@pytest.mark.parametrize("database", ["admin", "config"])
def test_listLocalSessions_database_independence(collection: Collection, database: str):
    """Test $listLocalSessions succeeds regardless of the target database."""
    db = collection.database.client[database]
    result = execute_command(
        db[collection.name],
        {"aggregate": 1, "pipeline": [{"$listLocalSessions": {}}], "cursor": {}},
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0)},
        msg=f"$listLocalSessions should succeed against the {database!r} database",
        raw_res=True,
    )
