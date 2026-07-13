"""Tests for abortTransaction command success behavior.

Each test drives the full transaction lifecycle inline (start session, start
transaction, run an operation, abort) so that setup -> act -> assert reads top
to bottom. These cover the fundamental abort behaviors: an aborted write is
rolled back, pre-transaction data survives the abort, an empty transaction
aborts, and the response carries ok:1.
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


def test_abortTransaction_rolls_back_insert(collection):
    """An aborted insert leaves no trace after the transaction aborts."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1, "x": "inserted"}, session=session)
        session.abort_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(readback, [])


def test_pre_existing_data_survives_abort(collection):
    """Documents inserted before the transaction survive an abort."""
    collection.insert_one({"_id": 1, "x": "seed"})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 2, "x": "txn"}, session=session)
        session.abort_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertSuccess(readback, [{"_id": 1, "x": "seed"}])


def test_abortTransaction_empty(collection):
    """Aborting a transaction with no operations succeeds."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        session.abort_transaction()
    readback = execute_command(collection, {"find": collection.name, "filter": {}})
    assertNotError(readback, msg="abortTransaction on an empty transaction should not error")


def test_abortTransaction_response_ok(collection):
    """The abortTransaction command response reports ok:1 on success."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        result = execute_admin_command(collection, {"abortTransaction": 1}, session=session)
    assertSuccessPartial(result, {"ok": 1.0})
