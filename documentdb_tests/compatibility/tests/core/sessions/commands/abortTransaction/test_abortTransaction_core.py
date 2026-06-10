"""Tests for abortTransaction command core behavior and success cases.

Validates fundamental command behavior including the no-transaction error,
admin database requirement, and parameter interactions. Also validates that
abortTransaction rolls back operations within a real transaction context,
including insert, update, delete, and multi-operation transactions, verifies
the response structure on success, and that pre-transaction data survives abort.
"""

from __future__ import annotations

import pytest
from bson import Binary, Int64

from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_command_test_case import (  # noqa: E501
    SessionCommandTestCase,
)
from documentdb_tests.compatibility.tests.core.sessions.commands.utils.session_test_case import (
    AbortSessionTestCase,
    SessionOp,
    SessionOperation,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertNotError,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import (
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    NO_SUCH_TRANSACTION_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_abort_session_command,
    execute_admin_command,
    execute_command,
)
from documentdb_tests.framework.parametrize import pytest_params

# ===========================================================================
# Outside-transaction error tests (admin db)
# ===========================================================================

pytestmark = pytest.mark.admin


# Property [No-Transaction Error]: abortTransaction outside a transaction fails.
CORE_NO_TRANSACTION_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "no_transaction_basic",
        command={"abortTransaction": 1},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction should fail with NoSuchTransaction outside a transaction",
    ),
]

# Property [Parameter Acceptance]: all valid parameters combined are syntactically accepted.
CORE_PARAMETER_ACCEPTANCE_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "all_valid_params",
        command={
            "abortTransaction": 1,
            "autocommit": False,
            "txnNumber": Int64(1),
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
            "comment": "full abort",
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction with all valid params should not produce a parsing error",
    ),
]

# Property [Parameter Interactions]: combinations of valid parameters behave correctly.
CORE_PARAMETER_INTERACTION_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "interaction_autocommit_only",
        command={"abortTransaction": 1, "autocommit": False},
        error_code=INVALID_OPTIONS_ERROR,
        msg="abortTransaction with autocommit:false only should fail with InvalidOptions",
    ),
    SessionCommandTestCase(
        "interaction_txn_number_only",
        command={"abortTransaction": 1, "txnNumber": Int64(1)},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction with txnNumber only should fail with IllegalOperation",
    ),
    SessionCommandTestCase(
        "interaction_autocommit_txn_number",
        command={"abortTransaction": 1, "autocommit": False, "txnNumber": Int64(1)},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="abortTransaction with autocommit + txnNumber should fail with IllegalOperation",
    ),
    SessionCommandTestCase(
        "interaction_lsid",
        command={"abortTransaction": 1, "lsid": {"id": Binary(b"\x00" * 16, 4)}},
        error_code=NO_SUCH_TRANSACTION_ERROR,
        msg="abortTransaction with explicit lsid should accept the field",
    ),
]

CORE_TESTS: list[SessionCommandTestCase] = (
    CORE_NO_TRANSACTION_TESTS + CORE_PARAMETER_ACCEPTANCE_TESTS + CORE_PARAMETER_INTERACTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CORE_TESTS))
def test_abortTransaction_core(collection, test):
    """Test abortTransaction core behavior."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Admin Database Requirement]: abortTransaction must run against the admin database.
ADMIN_DB_TESTS: list[SessionCommandTestCase] = [
    SessionCommandTestCase(
        "non_admin_database",
        command={"abortTransaction": 1},
        error_code=UNAUTHORIZED_ERROR,
        msg="abortTransaction on a non-admin database should fail with Unauthorized",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADMIN_DB_TESTS))
def test_abortTransaction_admin_db_required(collection, test):
    """Test abortTransaction requires admin database."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# ===========================================================================
# In-transaction success tests (replica_set)
# ===========================================================================


# ---------------------------------------------------------------------------
# Property [Abort Rollback]: aborted operations are rolled back.
# ---------------------------------------------------------------------------

ABORT_ROLLBACK_TESTS: list[AbortSessionTestCase] = [
    AbortSessionTestCase(
        "abort_insert",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1, "x": "inserted"})],
        expected=[],
        msg="abortTransaction should roll back the inserted document",
    ),
    AbortSessionTestCase(
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
    AbortSessionTestCase(
        "abort_delete",
        docs=[{"_id": 1, "x": "to_delete"}],
        ops=[SessionOperation(op=SessionOp.DELETE, filter={"_id": 1})],
        expected=[{"_id": 1, "x": "to_delete"}],
        msg="abortTransaction should roll back the deletion",
    ),
    AbortSessionTestCase(
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
    AbortSessionTestCase(
        "abort_with_writeconcern",
        docs=[{"_id": 1, "x": "before"}],
        ops=[
            SessionOperation(
                op=SessionOp.UPDATE,
                filter={"_id": 1},
                update={"$set": {"x": "after"}},
            )
        ],
        abort_command={"abortTransaction": 1, "writeConcern": {"w": 1}},
        expected=[{"_id": 1, "x": "before"}],
        msg="abortTransaction with writeConcern should roll back changes",
    ),
    AbortSessionTestCase(
        "abort_insert_delete_same_doc",
        ops=[
            SessionOperation(op=SessionOp.INSERT, document={"_id": 1}),
            SessionOperation(op=SessionOp.DELETE, filter={"_id": 1}),
        ],
        expected=[],
        msg="abortTransaction should roll back insert+delete of the same document",
    ),
    AbortSessionTestCase(
        "abort_multiple_inserts",
        ops=[
            SessionOperation(op=SessionOp.INSERT, document={"_id": 1}),
            SessionOperation(op=SessionOp.INSERT, document={"_id": 2}),
        ],
        expected=[],
        msg="abortTransaction should roll back multiple inserts",
    ),
    AbortSessionTestCase(
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


# ---------------------------------------------------------------------------
# Property [Pre-Transaction Data Survival]: seed data survives abort.
# ---------------------------------------------------------------------------

PRE_TRANSACTION_TESTS: list[AbortSessionTestCase] = [
    AbortSessionTestCase(
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


# ---------------------------------------------------------------------------
# Property [Empty Transaction]: aborting a transaction with no ops succeeds.
# ---------------------------------------------------------------------------

EMPTY_TRANSACTION_TESTS: list[AbortSessionTestCase] = [
    AbortSessionTestCase(
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


# ---------------------------------------------------------------------------
# Property [Response Structure]: abort response contains ok:1 on success.
# ---------------------------------------------------------------------------

RESPONSE_STRUCTURE_TESTS: list[AbortSessionTestCase] = [
    AbortSessionTestCase(
        "abort_response_ok",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        abort_command={"abortTransaction": 1},
        expected_response={"ok": 1.0},
        msg="abortTransaction response should have ok:1 on success",
    ),
    AbortSessionTestCase(
        "abort_with_comment",
        ops=[SessionOperation(op=SessionOp.INSERT, document={"_id": 1})],
        abort_command={"abortTransaction": 1, "comment": "test abort"},
        expected_response={"ok": 1.0},
        msg="abortTransaction with comment should succeed",
    ),
]


@pytest.mark.replica_set
@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_abortTransaction_core_response(collection, test):
    """Test abortTransaction returns expected response fields."""
    result = execute_abort_session_command(collection, test)
    assertSuccessPartial(result, test.expected_response, msg=test.msg)
