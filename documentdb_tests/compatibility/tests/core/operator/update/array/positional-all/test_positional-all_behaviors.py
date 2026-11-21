"""
Comprehensive tests for $[] (positional all) update operator.

Covers basic array updates, nested doc arrays, empty arrays, missing fields,
non-array fields, multi-document updates, upsert, command paths, and
composition conflicts.

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


# ---- happy path: basic $[] ---------------------------------------------------


def test_positional_all_multiplies_all_elements(collection):
    """$[] with $mul updates every element in the array."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3, 4]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$mul": {"items.$[]": 10}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [10, 20, 30, 40]}])


def test_positional_all_sets_nested_field_in_all_elements(collection):
    """$[] with $set updates a sub-field in every array element."""
    collection.insert_one({"_id": 1, "items": [{"v": 1}, {"v": 2}, {"v": 3}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"items.$[].v": 0}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"v": 0}, {"v": 0}, {"v": 0}]}])


def test_positional_all_replaces_nested_arrays(collection):
    """$[] replaces each sub-array element entirely."""
    collection.insert_one({"_id": 1, "a": [[1, 2], [3, 4]]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a.$[]": [99]}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": [[99], [99]]}])


def test_positional_all_inc_all_elements(collection):
    """$[] with $inc increments every element in the array."""
    collection.insert_one({"_id": 1, "scores": [10, 20, 30]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$inc": {"scores.$[]": 5}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "scores": [15, 25, 35]}])


# ---- empty array (no-op) ----------------------------------------------------


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason="pgmongo returns nModified=1 and inserts None into empty array; tracked: **NEEDS ADO ITEM**",
    raises=AssertionError,
)
def test_positional_all_on_empty_array_is_noop(collection):
    """$[] on an empty array is a no-op (nModified=0, array unchanged)."""
    collection.insert_one({"_id": 1, "items": []})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"items.$[].v": 99}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- multi -------------------------------------------------------------------


def test_positional_all_multi_updates_all_docs(collection):
    """$[] with multi:true updates all elements across all matched documents."""
    collection.insert_many([
        {"_id": 1, "scores": [10, 20]},
        {"_id": 2, "scores": [30, 40]},
    ])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$inc": {"scores.$[]": 1}}, "multi": True}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "scores": [11, 21]}, {"_id": 2, "scores": [31, 41]}])


# ---- command paths -----------------------------------------------------------


def test_positional_all_via_find_and_modify(collection):
    """$[] works through findAndModify and returns the updated document."""
    collection.insert_one({"_id": 1, "arr": [10, 20, 30]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$inc": {"arr.$[]": 5}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "arr": [15, 25, 35]}})


# ---- composition -------------------------------------------------------------


def test_positional_all_composes_with_set_on_different_path(collection):
    """$[] and $set on a different field both apply cleanly."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3], "status": "old"})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$inc": {"items.$[]": 10}, "$set": {"status": "new"}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [11, 12, 13], "status": "new"}])


# ---- error cases -------------------------------------------------------------


def test_positional_all_on_missing_field_fails(collection):
    """$[] on a path that does not exist in the document fails with code 2."""
    collection.insert_one({"_id": 1, "other": "x"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"items.$[].v": 99}}}],
        },
    )
    assertFailureCode(result, 2)


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason="pgmongo returns error code 28 instead of 2 for non-array field; tracked: **NEEDS ADO ITEM**",
    raises=AssertionError,
)
def test_positional_all_on_non_array_field_fails(collection):
    """$[] on a non-array field fails with BadValue (code 2)."""
    collection.insert_one({"_id": 1, "items": "not_an_array"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"items.$[].v": 99}}}],
        },
    )
    assertFailureCode(result, 2)


def test_positional_all_upsert_on_missing_doc_fails(collection):
    """$[] with upsert fails because the path must exist in the document."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 99}, "u": {"$set": {"items.$[].v": 1}}, "upsert": True}
            ],
        },
    )
    assertFailureCode(result, 2)


def test_positional_all_conflicts_with_same_path(collection):
    """$set + $inc on the same $[] path produces conflict (code 40)."""
    collection.insert_one({"_id": 1, "arr": [1, 2]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"arr.$[]": 0}, "$inc": {"arr.$[]": 1}}}
            ],
        },
    )
    assertFailureCode(result, 40)
