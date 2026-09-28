"""Tests for fsync invocation context: explicit session, authorization scope, and transactions."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import (
    OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_admin_command,
    execute_command,
)

pytestmark = pytest.mark.no_parallel


# Property [Explicit Session Accepted]: a no-lock flush issued under an explicit
# client session behaves identically to a sessionless invocation.
def test_fsync_accepts_explicit_session(collection):
    """Test fsync runs a no-lock flush under an explicit client session."""
    session = collection.database.client.start_session()
    try:
        result = execute_admin_command(collection, {"fsync": 1}, session=session)
        assertSuccessPartial(
            result,
            {"ok": 1.0, "numFiles": 1},
            msg="fsync should run a no-lock flush under an explicit session",
        )
    finally:
        session.end_session()


# Property [Authorization Scope]: fsync is admin-only, so running it against a
# non-admin database produces an Unauthorized error.
def test_fsync_rejects_non_admin_database(collection):
    """Test fsync rejects execution against a non-admin database."""
    result = execute_command(collection, {"fsync": 1})
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="fsync should reject a flush against a non-admin database",
    )


# Property [Multi-Document Transaction]: fsync is not supported inside a
# multi-document transaction and errors with OperationNotSupportedInTransaction.
@pytest.mark.requires(transactions=True)
def test_fsync_rejects_multi_document_transaction(collection):
    """Test fsync errors when issued inside a multi-document transaction."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        try:
            result = execute_admin_command(collection, {"fsync": 1}, session=session)
        finally:
            session.abort_transaction()
    assertFailureCode(
        result,
        OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="fsync should error when issued inside a multi-document transaction",
    )
