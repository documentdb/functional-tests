"""Tests for $push update command behavior.

Covers: updateOne, updateMany, upsert, bulkWrite.
"""

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command


def test_push_updateOne_response(collection):
    """Test $push with updateOne reports correct response."""
    collection.insert_one({"_id": 1, "arr": [1]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"arr": 2}}}],
        },
    )
    assertSuccessPartial(
        result, {"n": 1, "nModified": 1, "ok": 1.0}, msg="updateOne should report nModified=1"
    )


def test_push_updateOne_result(collection):
    """Test $push with updateOne produces correct document."""
    collection.insert_one({"_id": 1, "arr": [1]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"arr": 2}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "arr": [1, 2]}], msg="updateOne should append value")


def test_push_updateMany(collection):
    """Test $push with updateMany updates all matched docs."""
    collection.insert_many(
        [{"_id": 1, "arr": [1]}, {"_id": 2, "arr": [10]}, {"_id": 3, "arr": [100]}]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$push": {"arr": 99}}, "multi": True}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "arr": [1, 99]},
            {"_id": 2, "arr": [10, 99]},
            {"_id": 3, "arr": [100, 99]},
        ],
        msg="updateMany should push to each matched document",
    )


def test_push_upsert_creates_doc(collection):
    """Test $push with upsert:true creates document when not found."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 99}, "u": {"$push": {"arr": 5}}, "upsert": True}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 99}})
    assertSuccess(
        result,
        [{"_id": 99, "arr": [5]}],
        msg="Upsert should create doc with array containing the value",
    )


def test_push_upsert_with_each(collection):
    """Test $push with $each and upsert:true creates document with all values."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 99}, "u": {"$push": {"arr": {"$each": [1, 2, 3]}}}, "upsert": True}
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 99}})
    assertSuccess(
        result,
        [{"_id": 99, "arr": [1, 2, 3]}],
        msg="Upsert with $each should create doc with all values",
    )


def test_push_bulk_write_response(collection):
    """Test $push in bulkWrite reports correct response."""
    collection.insert_many([{"_id": 1, "arr": [1]}, {"_id": 2, "arr": [10]}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$push": {"arr": 2}}},
                {"q": {"_id": 2}, "u": {"$push": {"arr": 20}}},
            ],
        },
    )
    assertSuccessPartial(
        result, {"n": 2, "nModified": 2, "ok": 1.0}, msg="Bulk update should report nModified=2"
    )


def test_push_bulk_write_result(collection):
    """Test $push in bulkWrite produces correct documents."""
    collection.insert_many([{"_id": 1, "arr": [1]}, {"_id": 2, "arr": [10]}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$push": {"arr": 2}}},
                {"q": {"_id": 2}, "u": {"$push": {"arr": 20}}},
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [{"_id": 1, "arr": [1, 2]}, {"_id": 2, "arr": [10, 20]}],
        msg="Bulk update should push to each doc",
    )
