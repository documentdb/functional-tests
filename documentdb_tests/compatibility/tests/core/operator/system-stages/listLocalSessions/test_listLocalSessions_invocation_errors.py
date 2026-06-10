"""Tests for $listLocalSessions invocation errors: collection scope, transactions, apiStrict."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import (
    API_STRICT_ERROR,
    INVALID_NAMESPACE_ERROR,
    NOT_FIRST_STAGE_ERROR,
    OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Stage Position Errors]: $listLocalSessions must be the first pipeline stage,
# so it is rejected when it follows another $listLocalSessions.
LISTLOCALSESSIONS_NOT_FIRST_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "after_list_local_sessions",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": {}}, {"$listLocalSessions": {}}],
            "cursor": {},
        },
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$listLocalSessions should be rejected when it follows another $listLocalSessions",
    ),
]

# Property [Collection-Level Invocation Errors]: $listLocalSessions must run against the
# database via aggregate: 1, so collection-level invocation is rejected.
LISTLOCALSESSIONS_COLLECTION_LEVEL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_level",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$listLocalSessions": {}}],
            "cursor": {},
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="$listLocalSessions should be rejected when invoked at the collection level",
    ),
]

# Property [apiStrict Invocation Errors]: $listLocalSessions is not in Stable API V1,
# so it is rejected under apiStrict: true for every argument shape.
LISTLOCALSESSIONS_API_STRICT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"api_strict_{arg_id}",
        command={
            "aggregate": 1,
            "pipeline": [{"$listLocalSessions": arg}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
        error_code=API_STRICT_ERROR,
        msg=f"$listLocalSessions should be rejected under apiStrict for the {arg_id} "
        "argument shape",
    )
    for arg_id, arg in [
        ("empty", {}),
        ("all_users_true", {"allUsers": True}),
        ("users_filter", {"users": [{"user": "nobody", "db": "admin"}]}),
    ]
]

LISTLOCALSESSIONS_INVOCATION_ERROR_TESTS = (
    LISTLOCALSESSIONS_NOT_FIRST_ERROR_TESTS
    + LISTLOCALSESSIONS_COLLECTION_LEVEL_ERROR_TESTS
    + LISTLOCALSESSIONS_API_STRICT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(LISTLOCALSESSIONS_INVOCATION_ERROR_TESTS))
def test_listLocalSessions_invocation_error(
    database_client: Database, collection: Collection, test: CommandTestCase
):
    """Test $listLocalSessions stage invocation errors."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(target, test.build_command(ctx))
    assertResult(
        result, expected=test.build_expected(ctx), error_code=test.error_code, msg=test.msg
    )


# Property [Transaction Invocation Errors]: $listLocalSessions is rejected inside a
# multi-document transaction.
@pytest.mark.aggregate
def test_listLocalSessions_in_transaction(collection: Collection):
    """Test $listLocalSessions is rejected inside a multi-document transaction."""
    command = {
        "aggregate": 1,
        "pipeline": [{"$listLocalSessions": {}}],
        "cursor": {},
    }
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        result = execute_command(collection, command, session=session)
        session.abort_transaction()
    assertFailureCode(
        result,
        OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="$listLocalSessions should be rejected when run inside a transaction",
    )
