"""Tests for applyOps command core behavior: operation types, response structure,
and basic functionality."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import CappedCollection, SiblingCollection

pytestmark = [pytest.mark.requires(change_streams=True), pytest.mark.no_parallel]


# Property [Insert Operations]: applyOps inserts documents into existing
# collections via the "i" op type.
APPLYOPS_INSERT_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "insert_single_document",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}}],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should insert a single document",
    ),
    ReplicationTestCase(
        "insert_multiple_documents",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "a": 1}},
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 2, "a": 2}},
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 3, "a": 3}},
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should insert multiple documents",
    ),
    ReplicationTestCase(
        "insert_all_bson_types",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "i",
                    "ns": ctx.namespace,
                    "o": {
                        "_id": 1,
                        "int32": 42,
                        "int64": Int64(123_456_789),
                        "double": 3.14,
                        "decimal128": Decimal128("1.23"),
                        "string": "hello",
                        "bool": True,
                        "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                        "null": None,
                        "object": {"nested": "value"},
                        "array": [1, 2, 3],
                        "binary": Binary(b"\x00\x01"),
                        "objectid": ObjectId(),
                        "regex": Regex("abc", "i"),
                        "timestamp": Timestamp(1, 1),
                        "minkey": MinKey(),
                        "maxkey": MaxKey(),
                    },
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should insert a document with all BSON types",
    ),
    ReplicationTestCase(
        "insert_nested_document",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "i",
                    "ns": ctx.namespace,
                    "o": {
                        "_id": 1,
                        "a": {"b": {"c": {"d": 1}}},
                        "arr": [[1, 2], [3, 4]],
                        "mixed": {"x": [{"y": 1}, {"y": 2}]},
                    },
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should insert a nested document",
    ),
    ReplicationTestCase(
        "insert_duplicate_id",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 2}}],
        },
        expected={"ok": Eq(1.0), "applied": Eq(1)},
        msg="applyOps should succeed on duplicate _id insert",
    ),
    ReplicationTestCase(
        "insert_into_capped_collection",
        target_collection=CappedCollection(size=1_048_576),
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}}],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should insert into a capped collection",
    ),
]

# Property [Update Operations]: applyOps updates documents via the "u" op type.
APPLYOPS_UPDATE_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "update_existing_document",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"_id": 1, "x": 2, "y": 3},
                    "o2": {"_id": 1},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should update an existing document",
    ),
    ReplicationTestCase(
        "update_with_set_modifier",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"$v": 2, "diff": {"u": {"x": 2}}},
                    "o2": {"_id": 1},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should update with $v:2 diff format",
    ),
]

# Property [Delete Operations]: applyOps deletes documents via the "d" op type.
APPLYOPS_DELETE_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "delete_existing_document",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "applyOps": [{"op": "d", "ns": ctx.namespace, "o": {"_id": 1}}],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should delete an existing document",
    ),
    ReplicationTestCase(
        "delete_nonexistent_document",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "d", "ns": ctx.namespace, "o": {"_id": 999}}],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should succeed silently when deleting a non-existent document",
    ),
]

# Property [No-op Operations]: applyOps accepts no-op entries via the "n" op type.
APPLYOPS_NOOP_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "noop_operation",
        command=lambda ctx: {
            "applyOps": [{"op": "n", "ns": ctx.namespace, "o": {}}],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should accept no-op operation",
    ),
    ReplicationTestCase(
        "noop_with_arbitrary_o",
        command=lambda ctx: {
            "applyOps": [
                {"op": "n", "ns": ctx.namespace, "o": {"msg": "test message"}},
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should accept no-op with arbitrary o document",
    ),
]

# Property [Command Operations]: applyOps executes DDL commands via the "c" op type.
APPLYOPS_COMMAND_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "command_create_collection",
        docs=[],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "c",
                    "ns": f"{ctx.database}.$cmd",
                    "o": {"create": f"{ctx.collection}_applyops_create"},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should create a collection via command operation",
    ),
    ReplicationTestCase(
        "command_drop_collection",
        docs=[],
        siblings=[SiblingCollection(suffix="_applyops_drop")],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "c",
                    "ns": f"{ctx.database}.$cmd",
                    "o": {"drop": f"{ctx.collection}_applyops_drop"},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should drop a collection via command operation",
    ),
]

# Property [Empty Array]: applyOps succeeds with an empty operations array.
APPLYOPS_EMPTY_ARRAY_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "empty_ops_array",
        command=lambda ctx: {"applyOps": []},
        expected={"ok": Eq(1.0)},
        msg="applyOps should succeed with an empty operations array",
    ),
]

# Property [Unrecognized Field Acceptance]: unknown fields are silently ignored.
APPLYOPS_UNRECOGNIZED_FIELD_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "unrecognized_single_field",
        command=lambda ctx: {"applyOps": [], "unknownField": 1},
        expected={"ok": Eq(1.0)},
        msg="applyOps should ignore unrecognized fields",
    ),
    ReplicationTestCase(
        "unrecognized_multiple_fields",
        command=lambda ctx: {"applyOps": [], "foo": 1, "bar": "baz"},
        expected={"ok": Eq(1.0)},
        msg="applyOps should ignore multiple unrecognized fields",
    ),
    ReplicationTestCase(
        "unrecognized_dollar_prefix",
        command=lambda ctx: {"applyOps": [], "$unknown": 1},
        expected={"ok": Eq(1.0)},
        msg="applyOps should ignore dollar-prefixed unrecognized fields",
    ),
]

# Property [Response Structure]: applyOps returns ok, applied, and results
# fields reflecting the operations performed.
APPLYOPS_RESPONSE_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "response_empty_ops",
        command=lambda ctx: {"applyOps": []},
        expected={"ok": Eq(1.0), "applied": Eq(0), "results": Eq([])},
        msg="applyOps should return applied: 0 and results: [] for empty ops",
    ),
    ReplicationTestCase(
        "response_single_op",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}}],
        },
        expected={"ok": Eq(1.0), "applied": Eq(1), "results": Eq([True])},
        msg="applyOps should return applied: 1 and results: [True] for single insert",
    ),
    ReplicationTestCase(
        "response_multiple_ops",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "a": 1}},
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 2, "a": 2}},
            ],
        },
        expected={
            "ok": Eq(1.0),
            "applied": Eq(2),
            "results": Eq([True, True]),
        },
        msg="applyOps should return applied: 2 and results: [True, True] for two inserts",
    ),
    ReplicationTestCase(
        "response_noop_op",
        command=lambda ctx: {
            "applyOps": [{"op": "n", "ns": ctx.namespace, "o": {}}],
        },
        expected={"ok": Eq(1.0), "applied": Eq(0)},
        msg="applyOps should not count no-op in applied",
    ),
]

APPLYOPS_CORE_TESTS: list[ReplicationTestCase] = (
    APPLYOPS_INSERT_TESTS
    + APPLYOPS_UPDATE_TESTS
    + APPLYOPS_DELETE_TESTS
    + APPLYOPS_NOOP_TESTS
    + APPLYOPS_COMMAND_TESTS
    + APPLYOPS_EMPTY_ARRAY_TESTS
    + APPLYOPS_UNRECOGNIZED_FIELD_TESTS
    + APPLYOPS_RESPONSE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_CORE_TESTS))
def test_applyOps_core(database_client, collection, test):
    """Test applyOps command core behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    if test.use_admin:
        result = execute_admin_command(collection, test.build_command(ctx))
    else:
        result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Idempotent Operations]: applying the same operation twice succeeds.
APPLYOPS_IDEMPOTENT_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "idempotent_delete",
        docs=[{"_id": 1, "x": 1}],
        setup=lambda coll: execute_admin_command(
            coll,
            {"applyOps": [{"op": "d", "ns": f"{coll.database.name}.{coll.name}", "o": {"_id": 1}}]},
        ),
        command=lambda ctx: {
            "applyOps": [{"op": "d", "ns": ctx.namespace, "o": {"_id": 1}}],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should succeed silently when deleting an already-deleted document",
    ),
    ReplicationTestCase(
        "idempotent_insert",
        docs=[{"_id": 0, "setup": True}],
        setup=lambda coll: execute_admin_command(
            coll,
            {
                "applyOps": [
                    {
                        "op": "i",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 1, "x": 1},
                    }
                ]
            },
        ),
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 2}}],
        },
        expected={"ok": Eq(1.0), "applied": Eq(1), "results": Eq([True])},
        msg="applyOps should succeed on duplicate _id insert (second apply)",
    ),
    ReplicationTestCase(
        "idempotent_noop",
        docs=[],
        setup=lambda coll: execute_admin_command(
            coll,
            {"applyOps": [{"op": "n", "ns": f"{coll.database.name}.{coll.name}", "o": {}}]},
        ),
        command=lambda ctx: {
            "applyOps": [{"op": "n", "ns": ctx.namespace, "o": {}}],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should succeed when applying no-op twice",
    ),
]


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_IDEMPOTENT_TESTS))
def test_applyOps_idempotent(database_client, collection, test):
    """Test applyOps idempotent operations."""
    collection = test.prepare(database_client, collection)
    if test.setup:
        test.setup(collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Document Effect Verification]: applyOps operations produce the
# expected documents in the collection.
APPLYOPS_DOC_CHECK_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "doc_check_insert",
        docs=[{"_id": 0, "setup": True}],
        setup=lambda coll: execute_admin_command(
            coll,
            {
                "applyOps": [
                    {
                        "op": "i",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 1, "x": 1},
                    }
                ]
            },
        ),
        command=lambda ctx: {"find": ctx.collection, "filter": {"_id": 1}},
        use_admin=False,
        expected=[{"_id": 1, "x": 1}],
        msg="applyOps insert should create the document",
    ),
    ReplicationTestCase(
        "doc_check_update",
        docs=[{"_id": 1, "x": 1}],
        setup=lambda coll: execute_admin_command(
            coll,
            {
                "applyOps": [
                    {
                        "op": "u",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 1, "x": 2, "y": 3},
                        "o2": {"_id": 1},
                    }
                ]
            },
        ),
        command=lambda ctx: {"find": ctx.collection, "filter": {"_id": 1}},
        use_admin=False,
        expected=[{"_id": 1, "x": 2, "y": 3}],
        msg="applyOps update should modify the document",
    ),
    ReplicationTestCase(
        "doc_check_delete",
        docs=[{"_id": 1, "x": 1}],
        setup=lambda coll: execute_admin_command(
            coll,
            {
                "applyOps": [
                    {
                        "op": "d",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 1},
                    }
                ]
            },
        ),
        command=lambda ctx: {"find": ctx.collection, "filter": {"_id": 1}},
        use_admin=False,
        expected=[],
        msg="applyOps delete should remove the document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_DOC_CHECK_TESTS))
def test_applyOps_doc_check(database_client, collection, test):
    """Test applyOps operations produce the expected documents."""
    collection = test.prepare(database_client, collection)
    if test.setup:
        test.setup(collection)
    ctx = CommandContext.from_collection(collection)
    if test.use_admin:
        result = execute_admin_command(collection, test.build_command(ctx))
    else:
        result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
    )
