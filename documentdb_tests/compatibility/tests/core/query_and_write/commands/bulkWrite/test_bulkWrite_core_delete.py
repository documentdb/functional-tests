"""Tests for bulkWrite core delete operations."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

BULKWRITE_DELETE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_delete",
        docs=[{"_id": 1, "x": 1}],
        command={"bulkWrite": 1, "ops": [{"delete": 0, "filter": {"_id": 1}}]},
        expected={"ok": 1.0, "nDeleted": 1},
        msg="bulkWrite should perform a single delete",
    ),
    CommandTestCase(
        "delete_no_match",
        docs=[{"_id": 1, "x": 1}],
        command={"bulkWrite": 1, "ops": [{"delete": 0, "filter": {"_id": 999}}]},
        expected={"ok": 1.0, "nDeleted": 0},
        msg="bulkWrite delete with a non-matching filter should delete nothing",
    ),
    CommandTestCase(
        "delete_multi_true",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 1}, {"_id": 3, "x": 2}],
        command={"bulkWrite": 1, "ops": [{"delete": 0, "filter": {"x": 1}, "multi": True}]},
        expected={"ok": 1.0, "nDeleted": 2},
        msg="bulkWrite delete with multi:true should delete all matching documents",
    ),
    CommandTestCase(
        "delete_multi_false",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 1}],
        command={"bulkWrite": 1, "ops": [{"delete": 0, "filter": {"x": 1}, "multi": False}]},
        expected={"ok": 1.0, "nDeleted": 1},
        msg="bulkWrite delete with multi:false should delete only the first match",
    ),
    CommandTestCase(
        "delete_nonexistent_collection",
        command={"bulkWrite": 1, "ops": [{"delete": 0, "filter": {"x": 1}}]},
        expected={"ok": 1.0, "nDeleted": 0},
        msg="bulkWrite delete on a non-existent collection should delete nothing",
    ),
    CommandTestCase(
        "delete_empty_collection",
        docs=[],
        command={"bulkWrite": 1, "ops": [{"delete": 0, "filter": {"x": 1}}]},
        expected={"ok": 1.0, "nDeleted": 0},
        msg="bulkWrite delete on an empty collection should delete nothing",
    ),
    CommandTestCase(
        "insert_then_delete",
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "x": 1}},
                {"delete": 0, "filter": {"_id": 1}},
            ],
        },
        expected={"ok": 1.0, "nInserted": 1, "nDeleted": 1},
        msg="bulkWrite should insert then delete the same document",
    ),
    CommandTestCase(
        "delete_without_multi_deletes_one",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 1}, {"_id": 3, "x": 1}],
        command={"bulkWrite": 1, "ops": [{"delete": 0, "filter": {"x": 1}}]},
        expected={"ok": 1.0, "nDeleted": 1},
        msg="bulkWrite delete without the multi flag should delete only one document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_DELETE_TESTS))
def test_bulkWrite_core_delete(database_client, collection, test):
    """Test bulkWrite core delete operations."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


def test_bulkWrite_delete_namespace_isolation(collection):
    """Test delete targeting one namespace does not affect documents in a different namespace."""
    sibling = collection.database[f"{collection.name}_b"]
    sibling.drop()
    collection.insert_one({"_id": 1, "x": 1})
    sibling.insert_one({"_id": 1, "x": 1})
    ns_a = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [{"delete": 0, "filter": {"_id": 1}}],
            "nsInfo": [{"ns": ns_a}],
        },
    )
    other_ns = execute_command(sibling, {"find": sibling.name, "filter": {}})
    assertSuccess(other_ns, [{"_id": 1, "x": 1}])
    sibling.drop()
