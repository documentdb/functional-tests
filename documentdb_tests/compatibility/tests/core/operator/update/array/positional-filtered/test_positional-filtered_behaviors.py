"""
Comprehensive tests for $[<identifier>] positional-filtered update operator.

Covers basic array filter matching, scalar arrays, no-match no-ops,
multiple filters, nested paths, command paths (update, findAndModify),
multi-document updates, composition, and error cases.

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


# ---- happy path: basic filtering ---------------------------------------------


def test_positional_filtered_sets_matching_elements(collection):
    """$[<identifier>] with $set updates only elements matching the filter."""
    collection.insert_one({"_id": 1, "items": [{"v": 10}, {"v": 20}, {"v": 30}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {"_id": 1},
                "u": {"$set": {"items.$[elem].v": 0}},
                "arrayFilters": [{"elem.v": {"$gte": 20}}],
            }],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"v": 10}, {"v": 0}, {"v": 0}]}])


def test_positional_filtered_on_scalar_array(collection):
    """$[<identifier>] works on scalar (non-object) arrays with element-level filter."""
    collection.insert_one({"_id": 1, "nums": [1, 2, 3, 4, 5]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {"_id": 1},
                "u": {"$mul": {"nums.$[e]": 10}},
                "arrayFilters": [{"e": {"$gte": 3}}],
            }],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "nums": [1, 2, 30, 40, 50]}])


def test_positional_filtered_no_match_is_noop(collection):
    """$[<identifier>] where no elements match the filter is a no-op."""
    collection.insert_one({"_id": 1, "items": [{"v": 1}, {"v": 2}]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {"_id": 1},
                "u": {"$inc": {"items.$[elem].v": 10}},
                "arrayFilters": [{"elem.v": {"$gt": 100}}],
            }],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_positional_filtered_inc_matching_elements(collection):
    """$[<identifier>] with $inc increments only filtered elements."""
    collection.insert_one({"_id": 1, "scores": [{"s": 50}, {"s": 80}, {"s": 90}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {"_id": 1},
                "u": {"$inc": {"scores.$[e].s": 5}},
                "arrayFilters": [{"e.s": {"$gte": 80}}],
            }],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "scores": [{"s": 50}, {"s": 85}, {"s": 95}]}])


# ---- command paths -----------------------------------------------------------


def test_positional_filtered_via_find_and_modify(collection):
    """$[<identifier>] works via findAndModify."""
    collection.insert_one({"_id": 1, "items": [{"v": 1}, {"v": 5}, {"v": 10}]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"items.$[e].v": 99}},
            "arrayFilters": [{"e.v": {"$gte": 5}}],
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": [{"v": 1}, {"v": 99}, {"v": 99}]}})


def test_positional_filtered_multi_true(collection):
    """$[<identifier>] with multi:true updates filtered elements across documents."""
    collection.insert_many([
        {"_id": 1, "items": [{"v": 1}, {"v": 20}]},
        {"_id": 2, "items": [{"v": 30}, {"v": 2}]},
    ])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {},
                "u": {"$set": {"items.$[e].v": 0}},
                "arrayFilters": [{"e.v": {"$gte": 10}}],
                "multi": True,
            }],
        },
    )
    assertSuccessPartial(result, {"n": 2, "nModified": 2, "ok": 1.0})


# ---- composition -------------------------------------------------------------


def test_positional_filtered_composes_with_set_on_different_path(collection):
    """$[<identifier>] composes with $set on a different field."""
    collection.insert_one({"_id": 1, "items": [{"v": 5}, {"v": 15}], "x": "old"})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {"_id": 1},
                "u": {"$set": {"items.$[e].v": 0, "x": "new"}},
                "arrayFilters": [{"e.v": {"$gte": 10}}],
            }],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"v": 5}, {"v": 0}], "x": "new"}])


# ---- error cases -------------------------------------------------------------


def test_positional_filtered_missing_array_filters_fails(collection):
    """$[<identifier>] without arrayFilters option fails with BadValue (code 2)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {"_id": 1},
                "u": {"$set": {"items.$[elem]": 0}},
            }],
        },
    )
    assertFailureCode(result, 2)


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason="accepts invalid identifier names (starting with digit) instead of rejecting with code 2",
    raises=AssertionError,
)
def test_positional_filtered_invalid_identifier_fails(collection):
    """$[<identifier>] with non-alphanumeric identifier fails with BadValue (code 2)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {"_id": 1},
                "u": {"$set": {"items.$[123bad]": 0}},
                "arrayFilters": [{"123bad": {"$gte": 2}}],
            }],
        },
    )
    assertFailureCode(result, 2)


def test_positional_filtered_upsert_on_missing_path_fails(collection):
    """$[<identifier>] with upsert fails if the path doesn't exist (code 2)."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{
                "q": {"_id": 100},
                "u": {"$set": {"items.$[e].v": 0}},
                "arrayFilters": [{"e.v": {"$gte": 10}}],
                "upsert": True,
            }],
        },
    )
    assertFailureCode(result, 2)
