import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [nIndexesWas Response]: drop returns nIndexesWas reflecting the
# number of indexes on the collection at drop time.
DROP_NINDEXESWAS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "id_only",
        docs=[{"_id": 1}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 1, "ns": ctx.namespace, "ok": 1.0},
        msg="Should have nIndexesWas=1 for _id only",
    ),
    CommandTestCase(
        "one_additional",
        indexes=[IndexModel("a")],
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should have nIndexesWas=2 with one extra index",
    ),
    CommandTestCase(
        "multiple",
        indexes=[IndexModel("a"), IndexModel("b"), IndexModel("c")],
        docs=[{"_id": 1, "a": 1, "b": 1, "c": 1}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 4, "ns": ctx.namespace, "ok": 1.0},
        msg="Should have nIndexesWas=4 with 3 extra indexes",
    ),
]

# Property [Index Type Acceptance]: drop succeeds on collections with
# various index types and returns correct nIndexesWas.
DROP_INDEX_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "compound",
        indexes=[IndexModel([("a", 1), ("b", 1)])],
        docs=[{"_id": 1, "a": 1, "b": 1}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should have nIndexesWas=2 with compound index",
    ),
    CommandTestCase(
        "text",
        indexes=[IndexModel([("content", "text")])],
        docs=[{"_id": 1, "content": "hello world"}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with text index",
    ),
    CommandTestCase(
        "ttl",
        indexes=[IndexModel("createdAt", expireAfterSeconds=3600)],
        docs=[{"_id": 1, "createdAt": None}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with TTL index",
    ),
    CommandTestCase(
        "unique",
        indexes=[IndexModel("email", unique=True)],
        docs=[{"_id": 1, "email": "test"}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with unique index",
    ),
    CommandTestCase(
        "hashed",
        indexes=[IndexModel([("key", "hashed")])],
        docs=[{"_id": 1, "key": "value"}],
        command=lambda ctx: {"drop": ctx.collection},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with hashed index",
    ),
]

DROP_RESPONSE_TESTS: list[CommandTestCase] = DROP_NINDEXESWAS_TESTS + DROP_INDEX_TYPE_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_RESPONSE_TESTS))
def test_drop_response(database_client, collection, test):
    """Test drop command response fields."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
