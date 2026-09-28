"""Test cross-collection atomicity of an aborted transaction.

Writes to more than one collection in a single transaction are rolled back
atomically: after abort, neither collection retains its write.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_abort_rolls_back_writes_across_collections(collection):
    """Aborting rolls back writes made to a second collection in the same txn."""
    client = collection.database.client
    other = collection.database[f"{collection.name}_other"]
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        other.insert_one({"_id": 2}, session=session)
        session.abort_transaction()
    readback = execute_command(collection, {"find": other.name, "filter": {}})
    assertSuccess(readback, [])
