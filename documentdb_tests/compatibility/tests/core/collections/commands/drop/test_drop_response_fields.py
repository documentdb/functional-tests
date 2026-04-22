import pytest

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
        setup=lambda db: (
            db.create_collection("test_one_idx"),
            db["test_one_idx"].insert_one({"_id": 1, "a": 1}),
            db["test_one_idx"].create_index("a"),
            db["test_one_idx"],
        )[-1],
        command={"drop": "test_one_idx"},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should have nIndexesWas=2 with one extra index",
    ),
    CommandTestCase(
        "multiple",
        setup=lambda db: (
            db.create_collection("test_multi_idx"),
            db["test_multi_idx"].insert_one({"_id": 1, "a": 1, "b": 1, "c": 1}),
            db["test_multi_idx"].create_index("a"),
            db["test_multi_idx"].create_index("b"),
            db["test_multi_idx"].create_index("c"),
            db["test_multi_idx"],
        )[-1],
        command={"drop": "test_multi_idx"},
        expected=lambda ctx: {"nIndexesWas": 4, "ns": ctx.namespace, "ok": 1.0},
        msg="Should have nIndexesWas=4 with 3 extra indexes",
    ),
]

# Property [Index Type Acceptance]: drop succeeds on collections with
# various index types and returns correct nIndexesWas.
DROP_INDEX_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "compound",
        setup=lambda db: (
            db.create_collection("test_compound"),
            db["test_compound"].insert_one({"_id": 1, "a": 1, "b": 1}),
            db["test_compound"].create_index([("a", 1), ("b", 1)]),
            db["test_compound"],
        )[-1],
        command={"drop": "test_compound"},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should have nIndexesWas=2 with compound index",
    ),
    CommandTestCase(
        "text",
        setup=lambda db: (
            db.create_collection("test_text"),
            db["test_text"].insert_one({"_id": 1, "content": "hello world"}),
            db["test_text"].create_index([("content", "text")]),
            db["test_text"],
        )[-1],
        command={"drop": "test_text"},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with text index",
    ),
    CommandTestCase(
        "ttl",
        setup=lambda db: (
            db.create_collection("test_ttl"),
            db["test_ttl"].insert_one({"_id": 1, "createdAt": None}),
            db["test_ttl"].create_index("createdAt", expireAfterSeconds=3600),
            db["test_ttl"],
        )[-1],
        command={"drop": "test_ttl"},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with TTL index",
    ),
    CommandTestCase(
        "unique",
        setup=lambda db: (
            db.create_collection("test_unique"),
            db["test_unique"].insert_one({"_id": 1, "email": "test"}),
            db["test_unique"].create_index("email", unique=True),
            db["test_unique"],
        )[-1],
        command={"drop": "test_unique"},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with unique index",
    ),
    CommandTestCase(
        "hashed",
        setup=lambda db: (
            db.create_collection("test_hashed"),
            db["test_hashed"].insert_one({"_id": 1, "key": "value"}),
            db["test_hashed"].create_index([("key", "hashed")]),
            db["test_hashed"],
        )[-1],
        command={"drop": "test_hashed"},
        expected=lambda ctx: {"nIndexesWas": 2, "ns": ctx.namespace, "ok": 1.0},
        msg="Should succeed with hashed index",
    ),
]

DROP_RESPONSE_TESTS: list[CommandTestCase] = DROP_NINDEXESWAS_TESTS + DROP_INDEX_TYPE_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(DROP_RESPONSE_TESTS))
def test_drop_response(database_client, collection, test):
    """Test drop command response fields."""
    target = test.setup(database_client) if test.setup else collection
    if test.docs:
        target.insert_many(test.docs)
    ctx = CommandContext.from_collection(target)
    result = execute_command(target, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
