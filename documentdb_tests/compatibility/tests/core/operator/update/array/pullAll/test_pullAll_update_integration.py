"""Tests for $pullAll update command integration.

Covers: updateOne, updateMany, bulkWrite, upsert behavior, large arrays.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_pullAll_updateOne(collection):
    """Test $pullAll with updateOne removes multiple values from array."""
    collection.insert_one({"_id": 1, "a": [1, 2, 3, 4, 5]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"a": [2, 4]}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result, [{"_id": 1, "a": [1, 3, 5]}], msg="updateOne should remove multiple values"
    )


def test_pullAll_updateMany(collection):
    """Test $pullAll with updateMany processes each matched document independently."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [2, 3, 4]},
            {"_id": 3, "a": [5, 6, 7]},
        ]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$pullAll": {"a": [2, 3]}}, "multi": True}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "a": [1]},
            {"_id": 2, "a": [4]},
            {"_id": 3, "a": [5, 6, 7]},
        ],
        msg="updateMany should process each doc independently",
    )


def test_pullAll_bulkWrite(collection):
    """Test $pullAll in bulkWrite updates multiple documents correctly."""
    collection.insert_many(
        [
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [4, 5, 6]},
        ]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pullAll": {"a": [1]}}},
                {"q": {"_id": 2}, "u": {"$pullAll": {"a": [5, 6]}}},
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": [2, 3]}, {"_id": 2, "a": [4]}],
        msg="bulkWrite should update both docs correctly",
    )


def test_pullAll_upsert_creates_doc_without_array(collection):
    """Test $pullAll with upsert:true creates doc without array field."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 99}, "u": {"$pullAll": {"a": [1, 2]}}, "upsert": True}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 99}})
    assertSuccess(result, [{"_id": 99}], msg="Upsert should create doc without array field")


def test_pullAll_large_array(collection):
    """Test $pullAll removing many values from a large array."""
    large_array = list(range(200))
    collection.insert_one({"_id": 1, "a": large_array})
    values_to_remove = list(range(0, 200, 2))
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"a": values_to_remove}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "a": list(range(1, 200, 2))}],
        msg="Should remove even numbers from large array",
    )


def test_pullAll_large_values_list(collection):
    """Test $pullAll with large values list (100+ values)."""
    collection.insert_one({"_id": 1, "a": list(range(50))})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"a": list(range(150))}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result, [{"_id": 1, "a": []}], msg="Should remove all elements with large values list"
    )
