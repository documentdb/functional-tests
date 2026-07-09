"""Test that committing a transaction that was already aborted fails.

Once a transaction is aborted, sending commitTransaction for that same
transaction (same session id and txnNumber) fails with NoSuchTransaction. The
transaction is driven with explicit session fields so the same txnNumber can be
referenced across the start, abort, and commit commands. A dedicated client is
used for this hand-managed session so it does not disturb the shared client's
server-session pool (which would conflict with other tests under parallel runs).
"""

from __future__ import annotations

import uuid

import pytest
from bson import Binary, Int64
from pymongo import MongoClient

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_cannot_commit_after_abort(collection, connection_string):
    """Committing an already-aborted transaction fails with NoSuchTransaction."""
    lsid = {"id": Binary(uuid.uuid4().bytes, 4)}  # session id (UUID)
    txn_number = Int64(1)
    probe_client = MongoClient(connection_string)
    try:
        probe_collection = probe_client[collection.database.name][collection.name]
        execute_command(
            probe_collection,
            {
                "insert": collection.name,
                "documents": [{"_id": 1}],
                "lsid": lsid,
                "txnNumber": txn_number,
                "startTransaction": True,
                "autocommit": False,
            },
        )
        execute_admin_command(
            probe_collection,
            {"abortTransaction": 1, "lsid": lsid, "txnNumber": txn_number, "autocommit": False},
        )
        result = execute_admin_command(
            probe_collection,
            {"commitTransaction": 1, "lsid": lsid, "txnNumber": txn_number, "autocommit": False},
        )
    finally:
        probe_client.close()
    assertFailureCode(result, NO_SUCH_TRANSACTION_ERROR)
