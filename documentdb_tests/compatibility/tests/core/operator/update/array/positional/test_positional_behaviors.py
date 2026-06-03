"""
Comprehensive tests for $ (positional) update operator.

Covers basic array element matching, scalar arrays, $elemMatch queries,
nested arrays, multi-document updates, error conditions, and command paths.

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


# ---- happy path: basic positional update -------------------------------------


def test_positional_updates_matched_array_element(collection):
    """$ updates the first array element matched by the query condition."""
    collection.insert_one(
        {"_id": 1, "items": [{"name": "A", "v": 10}, {"name": "B", "v": 20}]}
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1, "items.name": "B"}, "u": {"$set": {"items.$.v": 99}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"name": "A", "v": 10}, {"name": "B", "v": 99}]}])


def test_positional_with_inc_on_scalar_array(collection):
    """$ with $inc updates the matched scalar array element."""
    collection.insert_one({"_id": 1, "scores": [10, 20, 30]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1, "scores": 20}, "u": {"$inc": {"scores.$": 5}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "scores": [10, 25, 30]}])


def test_positional_with_elemmatch_query(collection):
    """$ works with $elemMatch to target a specific sub-document."""
    collection.insert_one(
        {"_id": 1, "items": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1, "items": {"$elemMatch": {"x": 3}}},
                    "u": {"$set": {"items.$.y": 99}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"x": 1, "y": 2}, {"x": 3, "y": 99}]}])


# ---- nested arrays -----------------------------------------------------------


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason="positional $ matches wrong element when query targets nested array value",
)
def test_positional_with_nested_array_field(collection):
    """$ on a nested array replaces the matched element's sub-field."""
    collection.insert_one({"_id": 1, "a": [{"b": [1, 2]}, {"b": [3, 4]}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1, "a.b": 3}, "u": {"$set": {"a.$.b": [30, 40]}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": [{"b": [1, 2]}, {"b": [30, 40]}]}])


# ---- multi -------------------------------------------------------------------


def test_positional_multi_updates_first_match_per_doc(collection):
    """$ with multi:true updates the first matched element in each document."""
    collection.insert_many([
        {"_id": 1, "items": [{"v": 5}, {"v": 10}]},
        {"_id": 2, "items": [{"v": 15}, {"v": 10}]},
    ])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"items.v": 10}, "u": {"$set": {"items.$.v": 0}}, "multi": True}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "items": [{"v": 5}, {"v": 0}]},
            {"_id": 2, "items": [{"v": 15}, {"v": 0}]},
        ],
    )


# ---- command paths -----------------------------------------------------------


def test_positional_via_find_and_modify(collection):
    """$ works through findAndModify."""
    collection.insert_one({"_id": 1, "arr": [{"k": "a", "v": 1}, {"k": "b", "v": 2}]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"arr.k": "b"},
            "update": {"$set": {"arr.$.v": 99}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "arr": [{"k": "a", "v": 1}, {"k": "b", "v": 99}]}})


# ---- composition -------------------------------------------------------------


def test_positional_composes_with_set_on_different_path(collection):
    """$ and $set on a different field both apply cleanly."""
    collection.insert_one({"_id": 1, "items": [{"v": 10}, {"v": 20}], "status": "old"})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1, "items.v": 20},
                    "u": {"$set": {"items.$.v": 99, "status": "new"}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"v": 10}, {"v": 99}], "status": "new"}])


# ---- error cases -------------------------------------------------------------


def test_positional_without_array_query_fails(collection):
    """$ without an array query condition fails with BadValue (code 2)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"items.$.v": 99}}}],
        },
    )
    assertFailureCode(result, 2)


def test_positional_upsert_without_match_fails(collection):
    """$ with upsert on a non-existing doc fails (no array match possible)."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"items.v": 5}, "u": {"$set": {"items.$.v": 99}}, "upsert": True}
            ],
        },
    )
    assertFailureCode(result, 2)
