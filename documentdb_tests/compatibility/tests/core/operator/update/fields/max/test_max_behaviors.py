"""
Comprehensive tests for $max update operator.

Covers type comparison semantics, missing fields, cross-type ordering,
dates, NaN, nested paths, command paths (update, findAndModify),
multi-document updates, upsert, composition, and error cases.

Oracle: MongoDB 7.0.
SUT-agnostic: assertions follow observed MongoDB behavior; engine divergences
are tracked via `engine_xfail` markers with tracking links.
"""

import pytest
from bson import Int64
from datetime import datetime, timezone

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.update


# ---- happy path: comparison semantics ----------------------------------------


def test_max_replaces_when_supplied_is_higher(collection):
    """$max replaces existing value when supplied value is greater."""
    collection.insert_one({"_id": 1, "v": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": 20}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 20}])


def test_max_noop_when_supplied_is_lower(collection):
    """$max is a no-op when supplied value is less than existing."""
    collection.insert_one({"_id": 1, "v": 20})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": 5}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_max_noop_when_supplied_is_equal(collection):
    """$max is a no-op when supplied value equals existing."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": 10}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_max_creates_field_when_missing(collection):
    """$max creates the field when it does not exist (any value > missing)."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": 100}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 100}])


# ---- type coercion and cross-type -------------------------------------------


def test_max_int64_replaces_int32(collection):
    """$max with Int64 replaces smaller Int32."""
    collection.insert_one({"_id": 1, "v": 5})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": Int64(100)}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": Int64(100)}])


def test_max_cross_type_string_greater_than_int(collection):
    """$max with string replaces int (string > number in BSON type ordering)."""
    collection.insert_one({"_id": 1, "v": 100})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": "abc"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": "abc"}])


def test_max_date_replaces_earlier_date(collection):
    """$max with later date replaces earlier date."""
    collection.insert_one({"_id": 1, "v": datetime(2020, 1, 1, tzinfo=timezone.utc)})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": datetime(2025, 1, 1, tzinfo=timezone.utc)}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": datetime(2025, 1, 1, tzinfo=timezone.utc)}])


def test_max_nan_does_not_replace_finite(collection):
    """$max with NaN does not replace a finite value (NaN is not greater)."""
    collection.insert_one({"_id": 1, "v": 5.0})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": float("nan")}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- path semantics ----------------------------------------------------------


def test_max_nested_path(collection):
    """$max works on nested dotted paths."""
    collection.insert_one({"_id": 1, "a": {"b": 10}})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"a.b": 20}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"b": 20}}])


def test_max_creates_intermediate_path(collection):
    """$max creates intermediate documents for missing nested paths."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"a.b.c": 5}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"b": {"c": 5}}}])


# ---- command paths -----------------------------------------------------------


def test_max_via_find_and_modify(collection):
    """$max works via findAndModify command."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {"findAndModify": collection.name, "query": {"_id": 1}, "update": {"$max": {"v": 50}}, "new": True},
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "v": 50}})


def test_max_multi_true(collection):
    """$max with multi:true updates all matched documents."""
    collection.insert_many([{"_id": 1, "v": 5}, {"_id": 2, "v": 15}, {"_id": 3, "v": 25}])
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$max": {"v": 20}}, "multi": True}]},
    )
    assertSuccessPartial(result, {"n": 3, "nModified": 2, "ok": 1.0})


def test_max_upsert_creates_document(collection):
    """$max with upsert:true creates the document if none matches."""
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 99}, "u": {"$max": {"v": 42}}, "upsert": True}]},
    )
    doc = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}}
    )
    assertSuccess(doc, [{"_id": 99, "v": 42}])


# ---- composition -------------------------------------------------------------


def test_max_composes_with_inc_on_different_paths(collection):
    """$max composes with $inc on different fields."""
    collection.insert_one({"_id": 1, "a": 10, "b": 5})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"a": 20}, "$inc": {"b": 3}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": 20, "b": 8}])


# ---- error cases -------------------------------------------------------------


def test_max_conflicts_with_set_on_same_path(collection):
    """$max and $set on the same path produces ConflictingUpdateOperators."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": 20}, "$set": {"v": 5}}}]},
    )
    assertFailureCode(result, 40)
