"""Tests for $pull update command integration.

Covers: updateOne, updateMany, findAndModify, upsert, bulkWrite,
and interaction with other update operators.
"""

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command


def test_pull_update_many(collection):
    """Test $pull with updateMany processes each matched document."""
    collection.insert_many(
        [
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [2, 3, 4]},
            {"_id": 3, "arr": [3, 4, 5]},
        ]
    )
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$pull": {"arr": 3}}, "multi": True}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 3, "nModified": 3, "ok": 1.0},
        msg="Should update all matched docs",
    )


def test_pull_find_and_modify(collection):
    """Test $pull with findAndModify returns modified document."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3, 2]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$pull": {"arr": 2}},
            "new": True,
        },
    )
    assertSuccess(
        result,
        {"_id": 1, "arr": [1, 3]},
        raw_res=True,
        transform=lambda r: r["value"],
        msg="findAndModify should return updated doc",
    )


def test_pull_upsert_no_existing_doc(collection):
    """Test $pull with upsert:true when document does not exist creates doc without array field."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 99}, "u": {"$pull": {"arr": 1}}, "upsert": True}],
        },
    )
    find_result = execute_command(collection, {"find": collection.name, "filter": {"_id": 99}})
    assertSuccess(
        find_result, [{"_id": 99}], msg="Upsert with $pull should create doc without array field"
    )


def test_pull_different_conditions_different_fields(collection):
    """Test $pull with different conditions on different fields in same operation."""
    collection.insert_one({"_id": 1, "a": [1, 2, 3, 4, 5], "b": ["x", "y", "z"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"a": {"$gt": 3}, "b": "y"}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "a": [1, 2, 3], "b": ["x", "z"]}],
        msg="Should apply different conditions to different fields independently",
    )
