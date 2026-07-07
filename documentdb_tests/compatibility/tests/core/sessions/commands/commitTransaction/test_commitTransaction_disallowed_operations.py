"""Tests for operations that are not supported inside a transaction.

Which operation types may run inside a transaction is its own concern (kept out
of the behavioral files). A range of commands and aggregation stages are
rejected with OperationNotSupportedInTransaction when issued inside an active
transaction, as are writes to a capped collection or to a system database. Each
test issues the operation in the transaction and asserts the rejection; the
session is closed by its ``with`` block.
"""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(transactions=True)]


# Commands rejected inside a transaction with OperationNotSupportedInTransaction.
DISALLOWED_COMMANDS: list[CommandTestCase] = [
    CommandTestCase(
        "count",
        command=lambda ctx: {"count": ctx.collection},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="count command is not supported inside a transaction",
    ),
    CommandTestCase(
        "listCollections",
        command={"listCollections": 1},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="listCollections is not supported inside a transaction",
    ),
    CommandTestCase(
        "listIndexes",
        command=lambda ctx: {"listIndexes": ctx.collection},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="listIndexes is not supported inside a transaction",
    ),
    CommandTestCase(
        "explain",
        command=lambda ctx: {"explain": {"find": ctx.collection}},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="explain is not supported inside a transaction",
    ),
    CommandTestCase(
        "createUser",
        command={"createUser": "commit_txn_user", "pwd": "commit_txn_pwd", "roles": []},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="createUser is not supported inside a transaction",
    ),
    CommandTestCase(
        "getParameter",
        command={"getParameter": 1, "logLevel": 1},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="getParameter is not supported inside a transaction",
    ),
    CommandTestCase(
        "setParameter",
        command={"setParameter": 1, "logLevel": 0},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="setParameter is not supported inside a transaction",
    ),
    CommandTestCase(
        "killCursors",
        command=lambda ctx: {"killCursors": ctx.collection, "cursors": [Int64(0)]},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="killCursors is not supported as the first operation in a transaction",
    ),
    CommandTestCase(
        "hello",
        command={"hello": 1},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="hello is not supported as the first operation in a transaction",
    ),
    CommandTestCase(
        "buildInfo",
        command={"buildInfo": 1},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="buildInfo is not supported as the first operation in a transaction",
    ),
    CommandTestCase(
        "connectionStatus",
        command={"connectionStatus": 1},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="connectionStatus is not supported as the first operation in a transaction",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DISALLOWED_COMMANDS))
def test_command_disallowed_in_transaction(collection, test):
    """Commands not supported inside a transaction are rejected."""
    collection.insert_one({"_id": 1})
    ctx = CommandContext.from_collection(collection)
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(collection, test.build_command(ctx), session=session)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Aggregation stages rejected inside a transaction (run against the fixture
# collection via the aggregate command).
DISALLOWED_AGGREGATION_STAGES: list[CommandTestCase] = [
    CommandTestCase(
        "out",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$out": f"{ctx.collection}_out"}],
            "cursor": {},
        },
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$out is not supported inside a transaction",
    ),
    CommandTestCase(
        "merge",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$merge": {"into": f"{ctx.collection}_merge"}}],
            "cursor": {},
        },
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$merge is not supported inside a transaction",
    ),
    CommandTestCase(
        "unionWith",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$unionWith": ctx.collection}],
            "cursor": {},
        },
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$unionWith is not supported inside a transaction",
    ),
    CommandTestCase(
        "collStats",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$collStats": {"count": {}}}],
            "cursor": {},
        },
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$collStats is not supported inside a transaction",
    ),
    CommandTestCase(
        "indexStats",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$indexStats": {}}],
            "cursor": {},
        },
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$indexStats is not supported inside a transaction",
    ),
    CommandTestCase(
        "planCacheStats",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$planCacheStats": {}}],
            "cursor": {},
        },
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$planCacheStats is not supported inside a transaction",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DISALLOWED_AGGREGATION_STAGES))
def test_aggregation_stage_disallowed_in_transaction(collection, test):
    """Aggregation stages not supported inside a transaction are rejected."""
    collection.insert_one({"_id": 1})
    ctx = CommandContext.from_collection(collection)
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(collection, test.build_command(ctx), session=session)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Admin-level (database) aggregation stages rejected inside a transaction.
DISALLOWED_ADMIN_STAGES: list[CommandTestCase] = [
    CommandTestCase(
        "currentOp",
        command={"aggregate": 1, "pipeline": [{"$currentOp": {}}], "cursor": {}},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$currentOp is not supported inside a transaction",
    ),
    CommandTestCase(
        "listLocalSessions",
        command={"aggregate": 1, "pipeline": [{"$listLocalSessions": {}}], "cursor": {}},
        error_code=OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$listLocalSessions is not supported inside a transaction",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DISALLOWED_ADMIN_STAGES))
def test_admin_aggregation_stage_disallowed_in_transaction(collection, test):
    """Admin-level aggregation stages not supported inside a transaction are rejected."""
    collection.insert_one({"_id": 1})
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_admin_command(collection, test.command, session=session)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_write_to_capped_collection_disallowed_in_transaction(collection):
    """Writing to a capped collection inside a transaction is not supported."""
    capped = collection.database.create_collection(
        f"{collection.name}_capped", capped=True, size=4096
    )
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            collection,
            {"insert": capped.name, "documents": [{"_id": 1}]},
            session=session,
        )
    assertFailureCode(result, OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR)


@pytest.mark.parametrize("system_db_name", ["config", "local"])
def test_write_to_system_database_disallowed_in_transaction(collection, system_db_name):
    """Writing to a system database inside a transaction is not supported."""
    client = collection.database.client
    system_collection = client[system_db_name][f"{collection.name}_probe"]
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(
            system_collection,
            {"insert": system_collection.name, "documents": [{"_id": 1}]},
            session=session,
        )
    assertFailureCode(result, OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR)
