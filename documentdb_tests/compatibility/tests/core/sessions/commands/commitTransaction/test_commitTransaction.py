"""Tests for commitTransaction command success behavior.

Each test drives the full transaction lifecycle inline (start session, start
transaction, run an operation, commit) so that setup -> act -> assert reads
top to bottom. These cover the fundamental commit behaviors: a committed write
is durable, an empty transaction commits, the response carries ok:1, and a
commit is retryable.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import (
    assertNotError,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_commitTransaction_persists_insert(collection):
    """A committed insert is visible outside the transaction after commit."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1, "x": "inserted"}, session=session)
        session.commit_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(readback, [{"_id": 1, "x": "inserted"}])


def test_commitTransaction_empty(collection):
    """Committing a transaction with no operations succeeds."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        session.commit_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertNotError(readback, msg="commitTransaction on an empty transaction should not error")


def test_commitTransaction_response_ok(collection):
    """The commitTransaction command response reports ok:1 on success."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        result = execute_admin_command(collection, {"commitTransaction": 1}, session=session)
    assertSuccessPartial(result, {"ok": 1.0})


def test_commitTransaction_is_retryable(collection):
    """Re-sending commitTransaction after a successful commit returns ok:1.

    The committed state is retained for retryability, so the retry is a no-op
    that succeeds rather than an error.
    """
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        execute_admin_command(collection, {"commitTransaction": 1}, session=session)
        retry = execute_admin_command(collection, {"commitTransaction": 1}, session=session)
    assertSuccessPartial(retry, {"ok": 1.0})
