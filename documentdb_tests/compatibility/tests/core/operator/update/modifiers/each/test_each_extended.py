"""
Extended tests for $each modifier with $push and $addToSet.

Covers multiple values, empty array (noop), mixed types, non-array operand
error, $each with $addToSet (deduplication), nested subdocuments, upsert:true,
multi:true, findAndModify, and composition with other modifiers ($slice).

Oracle: MongoDB 7.0.
SUT-agnostic: assertions follow observed MongoDB behavior; engine divergences
are tracked via `engine_xfail` markers with tracking links.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.update


# ---- $push with $each: multiple values appended in order ---------------------


def test_each_push_appends_multiple_values_in_order(collection):
    """$push with $each appends all elements in the specified order."""
    collection.insert_one({"_id": 1, "items": ["A"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"items": {"$each": ["B", "C", "D"]}}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B", "C", "D"]}])


# ---- $push with $each: empty array is noop ----------------------------------


def test_each_push_empty_array_is_noop(collection):
    """$push with $each: [] does not modify the array."""
    collection.insert_one({"_id": 1, "items": [1, 2]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$push": {"items": {"$each": []}}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 2]}])


# ---- $push with $each: mixed types ------------------------------------------


def test_each_push_mixed_types(collection):
    """$push with $each can append values of mixed BSON types."""
    collection.insert_one({"_id": 1, "items": []})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {
                            "items": {
                                "$each": [1, "two", True, None, {"x": 1}]
                            }
                        }
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, "two", True, None, {"x": 1}]}])


# ---- $each with non-array value (error) --------------------------------------


def test_each_non_array_value_errors(collection):
    """$each with a non-array operand (string) fails with code 2."""
    collection.insert_one({"_id": 1, "items": [1]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"items": {"$each": "notarray"}}},
                }
            ],
        },
    )
    assertFailureCode(result, 2)


# ---- $addToSet with $each: deduplication -------------------------------------


def test_each_addToSet_deduplicates(collection):
    """$addToSet with $each only adds values not already present."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$addToSet": {"items": {"$each": [2, 3, 4, 5]}}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 2, 3, 4, 5]}])


# ---- $addToSet with $each: empty array is noop ------------------------------


def test_each_addToSet_empty_array_is_noop(collection):
    """$addToSet with $each: [] does not modify the array."""
    collection.insert_one({"_id": 1, "items": [1, 2]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$addToSet": {"items": {"$each": []}}}}
            ],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- $each with subdocuments ------------------------------------------------


def test_each_push_subdocuments(collection):
    """$push with $each can append multiple subdocuments."""
    collection.insert_one({"_id": 1, "items": []})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {
                            "items": {"$each": [{"a": 1}, {"a": 2}, {"a": 3}]}
                        }
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result, [{"_id": 1, "items": [{"a": 1}, {"a": 2}, {"a": 3}]}]
    )


# ---- $each with upsert:true -------------------------------------------------


def test_each_push_upsert_creates_document(collection):
    """$push with $each and upsert:true creates the document with the array."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 50},
                    "u": {"$push": {"items": {"$each": [1, 2, 3]}}},
                    "upsert": True,
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 50}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 50, "items": [1, 2, 3]}])


# ---- $each with multi:true ---------------------------------------------------


def test_each_push_multi_true(collection):
    """$push with $each and multi:true appends to all matched documents."""
    collection.insert_many(
        [{"_id": 1, "items": ["A"]}, {"_id": 2, "items": ["B"]}]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {},
                    "u": {"$push": {"items": {"$each": ["X", "Y"]}}},
                    "multi": True,
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "items": ["A", "X", "Y"]},
            {"_id": 2, "items": ["B", "X", "Y"]},
        ],
    )


# ---- $each with findAndModify ------------------------------------------------


def test_each_push_find_and_modify_post_image(collection):
    """$push with $each via findAndModify returns the post-update document."""
    collection.insert_one({"_id": 1, "items": [1]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$push": {"items": {"$each": [2, 3]}}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": [1, 2, 3]}})


# ---- $each with $slice (composition) ----------------------------------------


def test_each_with_slice_limits_array_size(collection):
    """$push with $each and $slice keeps only the last N elements."""
    collection.insert_one({"_id": 1, "items": [1, 2]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$push": {"items": {"$each": [3, 4, 5], "$slice": -3}}
                    },
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [3, 4, 5]}])


# ---- $each creates field if missing -----------------------------------------


def test_each_push_creates_field_when_missing(collection):
    """$push with $each on a missing field creates the field as a new array."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"items": {"$each": ["X", "Y"]}}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["X", "Y"]}])
