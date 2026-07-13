"""Test that an explicit writeConcern on an operation inside a transaction is rejected.

Per the MongoDB docs, setting a write concern on the individual write operations
inside a transaction returns an error; the write concern is set on the
transaction as a whole (on commit) instead.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_op_level_write_concern_rejected_in_transaction(collection):
    """An explicit writeConcern on a write operation inside a transaction is rejected."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {"insert": collection.name, "documents": [{"_id": 1}], "writeConcern": {"w": 1}},
            session=session,
        )
    assertFailureCode(result, INVALID_OPTIONS_ERROR)
