"""
Tests for update command sort option (MongoDB 8.0+).

Validates that sort determines which document is updated when multi:false,
and errors when combined with multi:true.
"""

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command


def test_update_sort_ascending_updates_lowest(collection):
    """Test sort:{field:1} updates document with lowest value."""
    collection.insert_many(
        [
            {"_id": 1, "x": 30},
            {"_id": 2, "x": 10},
            {"_id": 3, "x": 20},
        ]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$set": {"updated": True}}, "sort": {"x": 1}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 2}})
    assertSuccess(result, [{"_id": 2, "x": 10, "updated": True}])


def test_update_sort_descending_updates_highest(collection):
    """Test sort:{field:-1} updates document with highest value."""
    collection.insert_many(
        [
            {"_id": 1, "x": 30},
            {"_id": 2, "x": 10},
            {"_id": 3, "x": 20},
        ]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$set": {"updated": True}}, "sort": {"x": -1}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "x": 30, "updated": True}])


def test_update_sort_compound_key(collection):
    """Test sort with compound key {a:1, b:-1}."""
    collection.insert_many(
        [
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 5},
        ]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$set": {"hit": True}}, "sort": {"a": 1, "b": -1}}],
        },
    )
    # a=1 first, then b desc → _id=2 (a=1, b=20)
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 2}})
    assertSuccess(result, [{"_id": 2, "a": 1, "b": 20, "hit": True}])


def test_update_sort_with_multi_true_errors(collection):
    """Test sort combined with multi:true errors."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$set": {"x": 2}}, "sort": {"x": 1}, "multi": True}],
        },
    )
    assertFailureCode(result, FAILED_TO_PARSE_ERROR)


def test_update_sort_with_upsert_no_match(collection):
    """Test sort with upsert:true and no match still creates document."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"x": 1}},
                    "sort": {"x": 1},
                    "upsert": True,
                }
            ],
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {"_id": 1}}),
        [{"_id": 1, "x": 1}],
    )
