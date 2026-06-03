"""Tests for commitTransaction command success cases.

Validates that commitTransaction succeeds within a real transaction context,
including insert, update, delete, and multi-operation transactions. Also
verifies the response structure on success.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    SessionOp,
    SessionOperation,
    SessionTestCase,
)
from documentdb_tests.framework.assertions import assertNotError, assertSuccess
from documentdb_tests.framework.executor import execute_session_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.replica_set]


# ---------------------------------------------------------------------------
# Property [Commit Persistence]: committed operations are durable.
# ---------------------------------------------------------------------------

COMMIT_PERSISTENCE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "commit_insert",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1, "x": "inserted"})],
        expected=[{"_id": 1, "x": "inserted"}],
        msg="commitTransaction should persist the inserted document",
    ),
    SessionTestCase(
        "commit_update",
        docs=[{"_id": 1, "x": "before"}],
        ops=[
            SessionOperation(
                op=SessionOp.UPDATE,
                filter={"_id": 1},
                update={"$set": {"x": "after"}},
            )
        ],
        expected=[{"_id": 1, "x": "after"}],
        msg="commitTransaction should persist the updated value",
    ),
    SessionTestCase(
        "commit_delete",
        docs=[{"_id": 1, "x": "to_delete"}],
        ops=[SessionOperation(op=SessionOp.DELETE, filter={"_id": 1})],
        expected=[],
        msg="commitTransaction should persist the deletion",
    ),
    SessionTestCase(
        "commit_multi_operation",
        docs=[{"_id": 1, "x": "original"}],
        ops=[
            SessionOperation(op=SessionOp.INSERT, document={"_id": 2, "x": "new"}),
            SessionOperation(
                op=SessionOp.UPDATE,
                filter={"_id": 1},
                update={"$set": {"x": "modified"}},
            ),
        ],
        expected=[{"_id": 1, "x": "modified"}, {"_id": 2, "x": "new"}],
        msg="commitTransaction should persist all operations from a multi-op transaction",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMIT_PERSISTENCE_TESTS))
def test_commitTransaction_persistence(collection, test):
    """Test commitTransaction persists operations."""
    result = execute_session_command(collection, test)
    assertSuccess(
        result,
        {"cursor": {"firstBatch": test.expected}},
        msg=test.msg,
        raw_res=True,
        transform=lambda r: {"cursor": {"firstBatch": r["cursor"]["firstBatch"]}},
    )


# ---------------------------------------------------------------------------
# Property [Empty Transaction]: committing a transaction with no ops succeeds.
# ---------------------------------------------------------------------------

EMPTY_TRANSACTION_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "commit_empty_transaction",
        ops=[],
        msg="commitTransaction on empty transaction should not error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMPTY_TRANSACTION_TESTS))
def test_commitTransaction_empty(collection, test):
    """Test commitTransaction succeeds on an empty transaction."""
    result = execute_session_command(collection, test)
    assertNotError(result, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Response Structure]: commit response contains ok:1 on success.
# ---------------------------------------------------------------------------

RESPONSE_STRUCTURE_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "commit_response_ok",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1},
        expected_response={"ok": 1.0},
        msg="commitTransaction response should have ok:1 on success",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_commitTransaction_response(collection, test):
    """Test commitTransaction returns expected response fields."""
    result = execute_session_command(collection, test)
    assertSuccess(
        result,
        test.expected_response,
        msg=test.msg,
        raw_res=True,
        transform=lambda r: {"ok": r["ok"]},
    )


# ---------------------------------------------------------------------------
# Property [Commit with writeConcern]: explicit writeConcern is accepted.
# ---------------------------------------------------------------------------

COMMIT_WRITECONCERN_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "commit_with_writeconcern",
        docs=[{"_id": 1, "x": "before"}],
        ops=[
            SessionOperation(
                op=SessionOp.UPDATE,
                filter={"_id": 1},
                update={"$set": {"x": "after"}},
            )
        ],
        commit_command={"commitTransaction": 1, "writeConcern": {"w": 1}},
        expected=[{"_id": 1, "x": "after"}],
        msg="commitTransaction with writeConcern should persist changes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMIT_WRITECONCERN_TESTS))
def test_commitTransaction_writeconcern(collection, test):
    """Test commitTransaction succeeds with explicit writeConcern."""
    result = execute_session_command(collection, test)
    assertSuccess(
        result,
        {"cursor": {"firstBatch": test.expected}},
        msg=test.msg,
        raw_res=True,
        transform=lambda r: {"cursor": {"firstBatch": r["cursor"]["firstBatch"]}},
    )


# ---------------------------------------------------------------------------
# Property [Commit with comment]: comment parameter is accepted.
# ---------------------------------------------------------------------------

COMMIT_COMMENT_TESTS: list[SessionTestCase] = [
    SessionTestCase(
        "commit_with_comment",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        commit_command={"commitTransaction": 1, "comment": "test commit"},
        expected_response={"ok": 1.0},
        msg="commitTransaction with comment should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMMIT_COMMENT_TESTS))
def test_commitTransaction_comment(collection, test):
    """Test commitTransaction succeeds with comment parameter."""
    result = execute_session_command(collection, test)
    assertSuccess(
        result,
        test.expected_response,
        msg=test.msg,
        raw_res=True,
        transform=lambda r: {"ok": r["ok"]},
    )
