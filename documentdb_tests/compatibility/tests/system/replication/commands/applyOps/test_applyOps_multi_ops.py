"""Tests for applyOps multi-operation interactions and optional parameters.

Validates multi-op batches, cross-namespace operations, and
allowAtomic behavior.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import SiblingCollection

pytestmark = [pytest.mark.requires(change_streams=True), pytest.mark.no_parallel]


# Property [Multi-Operation Batches]: applyOps applies multiple operations
# in a single batch, combining insert, update, delete, and no-op ops.
APPLYOPS_MULTI_OPS_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "insert_then_update",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}},
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"_id": 1, "x": 2},
                    "o2": {"_id": 1},
                },
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should insert then update in one batch",
    ),
    ReplicationTestCase(
        "insert_then_delete",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}},
                {"op": "d", "ns": ctx.namespace, "o": {"_id": 1}},
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should insert then delete in one batch",
    ),
    ReplicationTestCase(
        "update_then_delete",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"_id": 1, "x": 2},
                    "o2": {"_id": 1},
                },
                {"op": "d", "ns": ctx.namespace, "o": {"_id": 1}},
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should update then delete in one batch",
    ),
    ReplicationTestCase(
        "multiple_inserts",
        docs=[{"_id": -1, "setup": True}],
        command=lambda ctx: {
            "applyOps": [
                {"op": "i", "ns": ctx.namespace, "o": {"_id": i, "x": i}} for i in range(5)
            ],
        },
        expected={"ok": Eq(1.0), "applied": Eq(5)},
        msg="applyOps should insert 5 documents",
    ),
    ReplicationTestCase(
        "mixed_op_types",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}},
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"_id": 1, "x": 2},
                    "o2": {"_id": 1},
                },
                {"op": "n", "ns": ctx.namespace, "o": {}},
                {"op": "d", "ns": ctx.namespace, "o": {"_id": 1}},
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should handle mixed operation types",
    ),
    ReplicationTestCase(
        "cross_namespace",
        docs=[],
        siblings=[SiblingCollection(suffix="_ns1"), SiblingCollection(suffix="_ns2")],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "i",
                    "ns": f"{ctx.database}.{ctx.collection}_ns1",
                    "o": {"_id": 1, "src": "coll1"},
                },
                {
                    "op": "i",
                    "ns": f"{ctx.database}.{ctx.collection}_ns2",
                    "o": {"_id": 1, "src": "coll2"},
                },
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should insert into multiple namespaces",
    ),
]

# Property [allowAtomic]: applyOps accepts the allowAtomic option with
# boolean values and defaults to true when omitted.
APPLYOPS_ALLOW_ATOMIC_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "allow_atomic_true",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}}],
            "allowAtomic": True,
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should accept allowAtomic: true",
    ),
    ReplicationTestCase(
        "allow_atomic_false",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}}],
            "allowAtomic": False,
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should accept allowAtomic: false",
    ),
    ReplicationTestCase(
        "allow_atomic_omitted",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1, "x": 1}}],
        },
        expected={"ok": Eq(1.0)},
        msg="applyOps should default allowAtomic to true",
    ),
]

# Property [allowAtomic Effectiveness]: allowAtomic: false allows partial
# commits when a later operation fails.
APPLYOPS_ATOMIC_EFFECTIVENESS_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "atomic_false_partial_commit",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "applyOps": [
                {"op": "i", "ns": ctx.namespace, "o": {"_id": 2, "x": 2}},
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"_id": 999, "x": 3},
                    "o2": {"_id": 999},
                },
            ],
            "allowAtomic": False,
        },
        error_code=UNKNOWN_ERROR,
        msg="applyOps with allowAtomic: false reports error when second op fails",
    ),
]

APPLYOPS_MULTI_OPS_AND_OPTIONS_TESTS: list[ReplicationTestCase] = (
    APPLYOPS_MULTI_OPS_TESTS + APPLYOPS_ALLOW_ATOMIC_TESTS + APPLYOPS_ATOMIC_EFFECTIVENESS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_MULTI_OPS_AND_OPTIONS_TESTS))
def test_applyOps_multi_ops(database_client, collection, test):
    """Test applyOps multi-operation interactions and optional parameters."""
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


# Property [Multi-Op Document Effect Verification]: multi-operation batches
# and allowAtomic produce the expected documents in the collection.
APPLYOPS_MULTI_OPS_DOC_CHECK_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "doc_check_insert_then_update",
        docs=[{"_id": 0, "setup": True}],
        setup=lambda coll: execute_admin_command(
            coll,
            {
                "applyOps": [
                    {
                        "op": "i",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 1, "x": 1},
                    },
                    {
                        "op": "u",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 1, "x": 2},
                        "o2": {"_id": 1},
                    },
                ]
            },
        ),
        command=lambda ctx: {"find": ctx.collection, "filter": {"_id": 1}},
        use_admin=False,
        expected=[{"_id": 1, "x": 2}],
        msg="applyOps should leave the updated document after insert-then-update",
    ),
    ReplicationTestCase(
        "doc_check_insert_then_delete",
        docs=[{"_id": 0, "setup": True}],
        setup=lambda coll: execute_admin_command(
            coll,
            {
                "applyOps": [
                    {
                        "op": "i",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 1, "x": 1},
                    },
                    {
                        "op": "d",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 1},
                    },
                ]
            },
        ),
        command=lambda ctx: {"find": ctx.collection, "filter": {"_id": 1}},
        use_admin=False,
        expected=[],
        msg="applyOps should leave no document after insert-then-delete",
    ),
    ReplicationTestCase(
        "doc_check_atomic_false_partial_commit",
        docs=[{"_id": 1, "x": 1}],
        setup=lambda coll: execute_admin_command(
            coll,
            {
                "applyOps": [
                    {
                        "op": "i",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 2, "x": 2},
                    },
                    {
                        "op": "u",
                        "ns": f"{coll.database.name}.{coll.name}",
                        "o": {"_id": 999, "x": 3},
                        "o2": {"_id": 999},
                    },
                ],
                "allowAtomic": False,
            },
        ),
        command=lambda ctx: {"find": ctx.collection, "filter": {"_id": 2}},
        use_admin=False,
        expected=[{"_id": 2, "x": 2}],
        msg="applyOps with allowAtomic: false should have committed the first insert",
    ),
]


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_MULTI_OPS_DOC_CHECK_TESTS))
def test_applyOps_multi_ops_doc_check(database_client, collection, test):
    """Test applyOps multi-operation document effects."""
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


def test_applyOps_cross_namespace_doc_check_ns1(database_client, collection):
    """Test applyOps cross-namespace insert creates document in first collection."""
    db = database_client
    coll_name = collection.name
    ns1 = f"{db.name}.{coll_name}_ns1"
    ns2 = f"{db.name}.{coll_name}_ns2"
    db.create_collection(f"{coll_name}_ns1")
    db.create_collection(f"{coll_name}_ns2")
    execute_admin_command(
        collection,
        {
            "applyOps": [
                {"op": "i", "ns": ns1, "o": {"_id": 1, "src": "coll1"}},
                {"op": "i", "ns": ns2, "o": {"_id": 1, "src": "coll2"}},
            ]
        },
    )
    coll1 = db[f"{coll_name}_ns1"]
    result = execute_command(coll1, {"find": coll1.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "src": "coll1"}],
        msg="applyOps should create document in first namespace",
    )


def test_applyOps_cross_namespace_doc_check_ns2(database_client, collection):
    """Test applyOps cross-namespace insert creates document in second collection."""
    db = database_client
    coll_name = collection.name
    ns1 = f"{db.name}.{coll_name}_ns1"
    ns2 = f"{db.name}.{coll_name}_ns2"
    db.create_collection(f"{coll_name}_ns1")
    db.create_collection(f"{coll_name}_ns2")
    execute_admin_command(
        collection,
        {
            "applyOps": [
                {"op": "i", "ns": ns1, "o": {"_id": 1, "src": "coll1"}},
                {"op": "i", "ns": ns2, "o": {"_id": 1, "src": "coll2"}},
            ]
        },
    )
    coll2 = db[f"{coll_name}_ns2"]
    result = execute_command(coll2, {"find": coll2.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "src": "coll2"}],
        msg="applyOps should create document in second namespace",
    )
