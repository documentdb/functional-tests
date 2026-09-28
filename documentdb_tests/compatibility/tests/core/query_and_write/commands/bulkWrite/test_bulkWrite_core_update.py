"""Tests for bulkWrite core update operations, filter edge cases, and multi-operation handling."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

BULKWRITE_UPDATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "single_update",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 20}}}],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite should perform a single update",
    ),
    CommandTestCase(
        "update_set_inc_unset",
        docs=[{"_id": 1, "x": 10, "y": 5, "z": 1}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": {"$set": {"x": 20}, "$inc": {"y": 1}, "$unset": {"z": ""}},
                }
            ],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite update should apply $set, $inc, and $unset operators",
    ),
    CommandTestCase(
        "update_pipeline",
        docs=[{"_id": 1, "x": 10, "y": 5}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": [{"$set": {"x": 99}}, {"$unset": "y"}],
                }
            ],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite update should accept an aggregation pipeline",
    ),
    CommandTestCase(
        "update_no_match",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 999}, "updateMods": {"$set": {"x": 20}}}],
        },
        expected={"ok": 1.0, "nMatched": 0, "nModified": 0},
        msg="bulkWrite update with a non-matching filter should match nothing",
    ),
    CommandTestCase(
        "update_multi_true",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 1}, {"_id": 3, "x": 2}],
        command={
            "bulkWrite": 1,
            "ops": [
                {"update": 0, "filter": {"x": 1}, "updateMods": {"$set": {"x": 99}}, "multi": True}
            ],
        },
        expected={"ok": 1.0, "nMatched": 2, "nModified": 2},
        msg="bulkWrite update with multi:true should update all matching documents",
    ),
    CommandTestCase(
        "update_multi_false",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 1}],
        command={
            "bulkWrite": 1,
            "ops": [
                {"update": 0, "filter": {"x": 1}, "updateMods": {"$set": {"x": 99}}, "multi": False}
            ],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite update with multi:false should update only the first match",
    ),
    CommandTestCase(
        "upsert_true_no_match",
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 100},
                    "updateMods": {"$set": {"x": 1}},
                    "upsert": True,
                }
            ],
        },
        expected={"ok": 1.0, "nUpserted": 1},
        msg="bulkWrite update with upsert:true and no match should insert a document",
    ),
    CommandTestCase(
        "update_nonexistent_collection",
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"x": 1}, "updateMods": {"$set": {"x": 2}}}],
        },
        expected={"ok": 1.0, "nMatched": 0, "nModified": 0},
        msg="bulkWrite update on a non-existent collection should match nothing",
    ),
    CommandTestCase(
        "update_empty_collection",
        docs=[],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"x": 1}, "updateMods": {"$set": {"x": 2}}}],
        },
        expected={"ok": 1.0, "nMatched": 0, "nModified": 0},
        msg="bulkWrite update on an empty collection should match nothing",
    ),
    CommandTestCase(
        "update_empty_filter_multi",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {}, "updateMods": {"$set": {"y": 1}}, "multi": True}],
        },
        expected={"ok": 1.0, "nMatched": 2, "nModified": 2},
        msg="bulkWrite update with an empty filter and multi:true should match all documents",
    ),
    CommandTestCase(
        "update_and_or_filter",
        docs=[{"_id": 1, "x": 1, "y": 1}, {"_id": 2, "x": 1, "y": 2}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"$and": [{"x": 1}, {"$or": [{"y": 1}]}]},
                    "updateMods": {"$set": {"z": 1}},
                }
            ],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite update should support $and/$or operators in the filter",
    ),
    CommandTestCase(
        "update_regex_filter",
        docs=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"name": {"$regex": "^A"}},
                    "updateMods": {"$set": {"matched": True}},
                }
            ],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite update should support a regex filter",
    ),
    CommandTestCase(
        "update_expr_filter",
        docs=[{"_id": 1, "x": 5}, {"_id": 2, "x": 15}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"$expr": {"$gt": ["$x", 10]}},
                    "updateMods": {"$set": {"big": True}},
                }
            ],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite update should support $expr in the filter",
    ),
    CommandTestCase(
        "large_batch_updates",
        docs=[{"_id": i, "x": i} for i in range(100)],
        command={
            "bulkWrite": 1,
            "ops": [
                {"update": 0, "filter": {"_id": i}, "updateMods": {"$set": {"x": i + 1}}}
                for i in range(100)
            ],
        },
        expected={"ok": 1.0, "nMatched": 100, "nModified": 100},
        msg="bulkWrite should apply a large batch of update operations",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_UPDATE_TESTS))
def test_bulkWrite_core_update(database_client, collection, test):
    """Test bulkWrite core update operations, filter edge cases, and multi-operation handling."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


def test_bulkWrite_sequential_ops_accumulate_on_same_document(collection):
    """Test multiple ops on the same document in one bulkWrite apply sequentially (x: 1->2->12)."""
    collection.insert_one({"_id": 1, "x": 1})
    ns = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 2}}},
                {"update": 0, "filter": {"_id": 1}, "updateMods": {"$inc": {"x": 10}}},
            ],
            "nsInfo": [{"ns": ns}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "x": 12}])


def test_bulkWrite_replacement_style_update_replaces_document(collection):
    """Test a replacement-style updateMods (no $ operators) replaces the whole document body."""
    collection.insert_one({"_id": 1, "x": 10, "y": 20, "z": 30})
    ns = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 1}, "updateMods": {"a": 1, "b": 2}}],
            "nsInfo": [{"ns": ns}],
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {"_id": 1}}),
        [{"_id": 1, "a": 1, "b": 2}],
        msg="bulkWrite replacement-style update should replace the body, removing non-_id fields",
    )


def test_bulkWrite_upsert_id_in_response(collection):
    """Test an upsert carries the upserted _id in cursor.firstBatch[].upserted._id."""
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 100},
                    "updateMods": {"$set": {"x": 1}},
                    "upsert": True,
                }
            ],
            "nsInfo": [{"ns": ns}],
        },
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "nUpserted": Eq(1),
            "cursor.firstBatch.0.upserted._id": Eq(100),
        },
        raw_res=True,
        msg="bulkWrite upsert should carry the upserted _id in cursor.firstBatch[].upserted._id",
    )
