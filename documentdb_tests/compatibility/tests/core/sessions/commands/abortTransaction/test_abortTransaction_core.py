"""Tests for abortTransaction command success cases.

Validates that abortTransaction rolls back operations within a real
transaction context, including insert, update, delete, and multi-operation
transactions, verifies the response structure on success, and that
pre-transaction data survives abort.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_test_case import (
    SessionOp,
    SessionOperation,
    SessionTestCase,
)
from documentdb_tests.framework.assertions import (
    assertNotError,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_abort_session_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin

# Property [Abort Rollback]: aborted operations are rolled back.
ABORT_ROLLBACK_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "abort_insert",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1, "x": "inserted"})],
        expected=[],
        msg="abortTransaction should roll back the inserted document",
    ),
    SessionTestCase(
        "abort_update",
        docs=[{"_id": 1, "x": "before"}],
        ops=[
            SessionOperation(
                op=SessionOp.UPDATE,
                filter={"_id": 1},
                update={"$set": {"x": "after"}},
            )
        ],
        expected=[{"_id": 1, "x": "before"}],
        msg="abortTransaction should roll back the updated value",
    ),
    SessionTestCase(
        "abort_delete",
        docs=[{"_id": 1, "x": "to_delete"}],
        ops=[SessionOperation(op=SessionOp.DELETE, filter={"_id": 1})],
        expected=[{"_id": 1, "x": "to_delete"}],
        msg="abortTransaction should roll back the deletion",
    ),
    SessionTestCase(
        "abort_multi_operation",
        docs=[{"_id": 1, "x": "original"}],
        ops=[
            SessionOperation(op=SessionOp.INSERT, document={"_id": 2, "x": "new"}),
            SessionOperation(
                op=SessionOp.UPDATE,
                filter={"_id": 1},
                update={"$set": {"x": "modified"}},
            ),
        ],
        expected=[{"_id": 1, "x": "original"}],
        msg="abortTransaction should roll back all operations from a multi-op transaction",
    ),
    SessionTestCase(
        "abort_insert_delete_same_doc",
        ops=[
            SessionOperation(op=SessionOp.INSERT, document={"_id": 1}),
            SessionOperation(op=SessionOp.DELETE, filter={"_id": 1}),
        ],
        expected=[],
        msg="abortTransaction should roll back insert+delete of the same document",
    ),
    SessionTestCase(
        "abort_multiple_inserts",
        ops=[
            SessionOperation(op=SessionOp.INSERT, document={"_id": 1}),
            SessionOperation(op=SessionOp.INSERT, document={"_id": 2}),
        ],
        expected=[],
        msg="abortTransaction should roll back multiple inserts",
    ),
    SessionTestCase(
        "abort_update_insert_different_docs",
        docs=[{"_id": 1, "x": "original"}],
        ops=[
            SessionOperation(
                op=SessionOp.UPDATE,
                filter={"_id": 1},
                update={"$set": {"x": "modified"}},
            ),
            SessionOperation(op=SessionOp.INSERT, document={"_id": 2, "x": "new"}),
        ],
        expected=[{"_id": 1, "x": "original"}],
        msg="abortTransaction should roll back update+insert of different documents",
    ),
]


@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(ABORT_ROLLBACK_TESTS))
def test_abortTransaction_core_rollback(collection, test):
    """Test abortTransaction rolls back operations."""
    result = execute_abort_session_command(collection, test)
    assertSuccess(result, test.expected, msg=test.msg)


# Property [Pre-Transaction Data Survival]: seed data survives abort.
PRE_TRANSACTION_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "pre_existing_data_survives",
        docs=[{"_id": 1, "x": "seed"}],
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 2, "x": "txn"})],
        expected=[{"_id": 1, "x": "seed"}],
        msg="Pre-existing documents should survive abort",
    ),
]


@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(PRE_TRANSACTION_TESTS))
def test_abortTransaction_core_pre_transaction_data(collection, test):
    """Test pre-transaction data survives abort."""
    result = execute_abort_session_command(collection, test)
    assertSuccess(result, test.expected, msg=test.msg)


# Property [Empty Transaction]: aborting a transaction with no ops succeeds.
EMPTY_TRANSACTION_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "abort_empty_transaction",
        ops=[],
        msg="abortTransaction on empty transaction should not error",
    ),
]


@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(EMPTY_TRANSACTION_TESTS))
def test_abortTransaction_core_empty(collection, test):
    """Test abortTransaction succeeds on an empty transaction."""
    result = execute_abort_session_command(collection, test)
    assertNotError(result, msg=test.msg)


# Property [Response Structure]: abort response contains ok:1 on success.
RESPONSE_STRUCTURE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "abort_response_ok",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"abortTransaction": 1},
        expected_response={"ok": 1.0},
        msg="abortTransaction response should have ok:1 on success",
    ),
]


@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_abortTransaction_core_response(collection, test):
    """Test abortTransaction returns expected response fields."""
    result = execute_abort_session_command(collection, test)
    assertSuccessPartial(result, test.expected_response, msg=test.msg)
