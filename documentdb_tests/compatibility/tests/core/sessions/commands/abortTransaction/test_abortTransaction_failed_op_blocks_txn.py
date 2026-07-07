"""Test that a failed operation blocks the rest of the transaction.

After a write inside a transaction fails (here, a duplicate-key error), the
transaction is aborted by the server, so a later operation in the same
transaction fails with NoSuchTransaction. The transaction must be aborted and
restarted to recover (covered separately).
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import NO_SUCH_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_failed_op_blocks_rest_of_transaction(collection):
    """A later op after a failed op in the same transaction fails with NoSuchTransaction."""
    collection.insert_one({"_id": 1})  # pre-existing doc so the txn insert collides
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        # Duplicate-key write (11000) fails and aborts the transaction.
        execute_command(
            collection,
            {"insert": collection.name, "documents": [{"_id": 1}]},
            session=session,
        )
        later = execute_command(
            collection,
            {"insert": collection.name, "documents": [{"_id": 2}]},
            session=session,
        )
    assertFailureCode(later, NO_SUCH_TRANSACTION_ERROR)
