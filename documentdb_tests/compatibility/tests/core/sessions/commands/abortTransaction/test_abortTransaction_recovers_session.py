"""Test that aborting recovers a session after a failed operation.

After a write inside a transaction fails and the transaction is aborted, the
same session can start and commit a fresh transaction successfully.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_abort_recovers_session_for_new_transaction(collection):
    """After a failed op and abort, the same session can run a new transaction."""
    collection.insert_one({"_id": 1})  # pre-existing doc so the first txn insert collides
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        # Duplicate-key write fails and aborts the transaction.
        execute_command(
            collection,
            {"insert": collection.name, "documents": [{"_id": 1}]},
            session=session,
        )
        session.abort_transaction()
        # The same session starts a fresh transaction and commits successfully.
        session.start_transaction()
        collection.insert_one({"_id": 2, "x": "recovered"}, session=session)
        session.commit_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {"_id": 2}})
    assertSuccess(readback, [{"_id": 2, "x": "recovered"}])
