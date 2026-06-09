"""Tests for $currentOp invocation constraints: namespace, pipeline position,
and transaction context."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_NAMESPACE_ERROR,
    NOT_FIRST_STAGE_ERROR,
    OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command


# Property [Non-Admin Database Rejected]: $currentOp against a database other
# than admin is rejected as an invalid namespace.
@pytest.mark.aggregate
def test_currentOp_rejects_non_admin_database(collection):
    """Test $currentOp is rejected when run against a database other than admin."""
    result = execute_command(
        collection,
        {"aggregate": 1, "pipeline": [{"$currentOp": {}}], "cursor": {}},
    )
    assertResult(
        result,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$currentOp should reject running against a database other than admin",
        raw_res=True,
    )


# Property [Named Collection Rejected]: $currentOp run as the named-collection
# aggregate form is rejected as an invalid namespace.
@pytest.mark.aggregate
def test_currentOp_rejects_named_collection(collection):
    """Test $currentOp is rejected when run as the named-collection aggregate form."""
    result = execute_admin_command(
        collection,
        {
            "aggregate": "currentOp_named_collection",
            "pipeline": [{"$currentOp": {}}],
            "cursor": {},
        },
    )
    assertResult(
        result,
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$currentOp should reject the named-collection aggregate form",
        raw_res=True,
    )


# Property [First Stage Constraint]: $currentOp appearing anywhere other than
# the first position in a pipeline is rejected. A second $currentOp after a
# leading one isolates the ordering error without first tripping the namespace
# constraint that a non-$currentOp leading stage would raise under admin.
@pytest.mark.aggregate
def test_currentOp_rejects_non_first_stage(collection):
    """Test $currentOp is rejected when it is not the first stage in a pipeline."""
    result = execute_admin_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [{"$currentOp": {}}, {"$currentOp": {}}],
            "cursor": {},
        },
    )
    assertResult(
        result,
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$currentOp should reject appearing as a non-first pipeline stage",
        raw_res=True,
    )


# Property [Transaction Context Rejected]: $currentOp run inside a
# multi-document transaction is rejected with OperationNotSupportedInTransaction.
@pytest.mark.aggregate
@pytest.mark.replica_set
def test_currentOp_in_transaction_error(collection):
    """Test $currentOp is rejected when run inside a multi-document transaction."""
    collection.insert_one({"_id": 1, "v": 0})
    client = collection.database.client
    session = client.start_session()
    session.start_transaction()
    try:
        collection.update_one({"_id": 1}, {"$set": {"v": 1}}, session=session)
        result = execute_admin_command(
            collection,
            {"aggregate": 1, "pipeline": [{"$currentOp": {}}], "cursor": {}},
            session=session,
        )
    finally:
        session.abort_transaction()
        session.end_session()
    assertResult(
        result,
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$currentOp should be rejected inside a multi-document transaction",
        raw_res=True,
    )
