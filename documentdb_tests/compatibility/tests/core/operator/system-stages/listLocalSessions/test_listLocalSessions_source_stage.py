"""Tests for $listLocalSessions source-stage behavior: output shape and database independence."""

from __future__ import annotations

import pytest
from bson.binary import UUID_SUBTYPE
from pymongo.collection import Collection

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import (
    BinarySubtype,
    ByteLen,
    Eq,
    IsType,
)


# Property [Return Type / Output Shape]: each session document is {_id: {id, uid}, lastUse},
# with id a UUID Binary (subtype 4), uid a 32-byte Binary, and lastUse a date.
@pytest.mark.aggregate
def test_listLocalSessions_output_shape(collection: Collection):
    """Test $listLocalSessions session document shape."""
    # Run inside an explicit session so the local session cache holds at least
    # one entry whose shape can be validated.
    with collection.database.client.start_session() as session:
        collection.database.command("ping", session=session)
        result = execute_command(
            collection,
            {"aggregate": 1, "pipeline": [{"$listLocalSessions": {}}], "cursor": {}},
            session=session,
        )
    assertResult(
        result,
        expected={
            "_id": {
                "id": BinarySubtype(UUID_SUBTYPE),
                "uid": ByteLen(32),
            },
            "lastUse": IsType("date"),
        },
        msg="$listLocalSessions returns documents shaped as {_id: {id, uid}, lastUse}",
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
