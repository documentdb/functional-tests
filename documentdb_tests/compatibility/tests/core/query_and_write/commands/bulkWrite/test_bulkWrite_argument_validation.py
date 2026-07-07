"""Tests for bulkWrite argument acceptance — valid ops, nsInfo, and optional fields."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

BULKWRITE_ARGUMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ops_single_operation",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}]},
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should accept ops with a single operation",
    ),
    CommandTestCase(
        "ops_many_operations",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": i}} for i in range(50)],
        },
        expected={"ok": 1.0, "nInserted": 50},
        msg="bulkWrite should accept ops with many operations",
    ),
    CommandTestCase(
        "let_with_document",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"$expr": {"$eq": ["$x", "$$targetVal"]}},
                    "updateMods": {"$set": {"matched": True}},
                }
            ],
            "let": {"targetVal": 10},
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite should accept a let document with variables",
    ),
    CommandTestCase(
        "ops_only_updates",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command={
            "bulkWrite": 1,
            "ops": [
                {"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 10}}},
                {"update": 0, "filter": {"_id": 2}, "updateMods": {"$set": {"x": 20}}},
            ],
        },
        expected={"ok": 1.0, "nMatched": 2, "nModified": 2},
        msg="bulkWrite should accept an ops array of only updates",
    ),
    CommandTestCase(
        "ops_only_deletes",
        docs=[{"_id": 1}, {"_id": 2}],
        command={
            "bulkWrite": 1,
            "ops": [
                {"delete": 0, "filter": {"_id": 1}},
                {"delete": 0, "filter": {"_id": 2}},
            ],
        },
        expected={"ok": 1.0, "nDeleted": 2},
        msg="bulkWrite should accept an ops array of only deletes",
    ),
    CommandTestCase(
        "writeConcern_valid",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "writeConcern": {"w": 1},
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should accept a valid writeConcern",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_ARGUMENT_TESTS))
def test_bulkWrite_argument_validation(database_client, collection, test):
    """Test bulkWrite argument acceptance — valid ops, nsInfo, and optional fields."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


def test_bulkWrite_accepts_unused_nsInfo_entry(collection):
    """Test bulkWrite accepts an nsInfo array with more namespaces than the ops reference."""
    ns = f"{collection.database.name}.{collection.name}"
    ns_unused = f"{collection.database.name}.{collection.name}_unused"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "nsInfo": [{"ns": ns}, {"ns": ns_unused}],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "nInserted": 1},
        msg="bulkWrite should accept an nsInfo entry that no op references",
    )
