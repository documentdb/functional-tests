"""Test write-conflict behavior for concurrent transactions.

When two open transactions write to the same document, the second writer fails
immediately with WriteConflict rather than blocking (first-committer-wins). The
first transaction commits; the conflicting session is left for its ``with``
block to close.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import WRITE_CONFLICT_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_second_writer_to_open_doc_fails_with_write_conflict(collection):
    """A second writer to a doc already modified in an open txn fails with WriteConflict."""
    collection.insert_one({"_id": 1, "x": 0})
    client = collection.database.client
    with client.start_session() as first, client.start_session() as second:
        first.start_transaction()
        collection.update_one({"_id": 1}, {"$set": {"x": 1}}, session=first)
        second.start_transaction()
        result = execute_command(
            collection,
            {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2}}}]},
            session=second,
        )
        first.commit_transaction()
    assertFailureCode(result, WRITE_CONFLICT_ERROR)
