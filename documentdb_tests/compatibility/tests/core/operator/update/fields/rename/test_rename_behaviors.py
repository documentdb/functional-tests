"""
Comprehensive tests for $rename update operator.

Covers basic renames, nested paths, missing fields, error conditions,
command paths (update, findAndModify), multi-document updates, upsert,
and composition conflicts.

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


# ---- happy path: basic rename ------------------------------------------------


def test_rename_basic_top_level_field(collection):
    """$rename moves a top-level field to a new name."""
    collection.insert_one({"_id": 1, "a": 10, "b": 20})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"a": "c"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "b": 20, "c": 10}])


def test_rename_overwrites_existing_destination(collection):
    """$rename to an existing field name overwrites the destination."""
    collection.insert_one({"_id": 1, "src": 42, "dst": "old"})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"src": "dst"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "dst": 42}])


# ---- missing field (no-op) ---------------------------------------------------


def test_rename_missing_source_is_noop(collection):
    """$rename on a non-existent source field is a no-op (nModified=0)."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"nonexist": "y"}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- nested paths ------------------------------------------------------------


def test_rename_nested_field_within_same_parent(collection):
    """$rename moves a nested field to another key under the same parent."""
    collection.insert_one({"_id": 1, "a": {"b": 5, "c": 6}})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"a.b": "a.d"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"c": 6, "d": 5}}])


def test_rename_top_level_to_nested_destination(collection):
    """$rename can move a top-level field into a nested path, creating intermediates."""
    collection.insert_one({"_id": 1, "x": 99})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"x": "a.b"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"b": 99}}])


# ---- command paths -----------------------------------------------------------


def test_rename_via_find_and_modify(collection):
    """$rename works through findAndModify and returns the updated document."""
    collection.insert_one({"_id": 1, "x": 42})
    result = execute_command(
        collection,
        {"findAndModify": collection.name, "query": {"_id": 1}, "update": {"$rename": {"x": "y"}}, "new": True},
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "y": 42}})


# ---- multi and upsert --------------------------------------------------------


def test_rename_multi_true_renames_across_documents(collection):
    """$rename with multi:true applies to all matched documents."""
    collection.insert_many([
        {"_id": 1, "old": "a"},
        {"_id": 2, "old": "b"},
        {"_id": 3, "old": "c"},
    ])
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$rename": {"old": "new"}}, "multi": True}]},
    )
    assertSuccessPartial(result, {"n": 3, "nModified": 3, "ok": 1.0})


def test_rename_multi_true_result_values(collection):
    """$rename with multi:true produces correct documents."""
    collection.insert_many([
        {"_id": 1, "old": "a"},
        {"_id": 2, "old": "b"},
    ])
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$rename": {"old": "new"}}, "multi": True}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "new": "a"}, {"_id": 2, "new": "b"}])


def test_rename_upsert_creates_doc_without_renamed_field(collection):
    """$rename with upsert on missing doc creates doc without the renamed field."""
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 50}, "u": {"$rename": {"a": "b"}}, "upsert": True}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_rename_upsert_doc_contents(collection):
    """$rename with upsert produces a doc with only _id (source missing)."""
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 50}, "u": {"$rename": {"a": "b"}}, "upsert": True}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 50}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 50}])


# ---- composition -------------------------------------------------------------


def test_rename_composes_with_set_on_different_paths(collection):
    """$rename and $set on different fields both apply cleanly."""
    collection.insert_one({"_id": 1, "a": 10, "c": "keep"})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$rename": {"a": "b"}, "$set": {"c": "updated"}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "b": 10, "c": "updated"}])


# ---- error cases -------------------------------------------------------------


def test_rename_id_field_fails(collection):
    """$rename from _id fails with ImmutableField (code 66)."""
    collection.insert_one({"_id": 1, "a": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"_id": "newid"}}}]},
    )
    assertFailureCode(result, 66)


def test_rename_to_id_field_fails(collection):
    """$rename to _id fails with ImmutableField (code 66)."""
    collection.insert_one({"_id": 1, "a": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"a": "_id"}}}]},
    )
    assertFailureCode(result, 66)


def test_rename_non_string_destination_fails(collection):
    """$rename with a non-string destination value fails with BadValue (code 2)."""
    collection.insert_one({"_id": 1, "a": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"a": 123}}}]},
    )
    assertFailureCode(result, 2)


def test_rename_to_empty_string_fails(collection):
    """$rename to an empty string path fails with EmptyFieldName (code 56)."""
    collection.insert_one({"_id": 1, "a": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"a": ""}}}]},
    )
    assertFailureCode(result, 56)


def test_rename_conflicts_with_set_on_same_source_path(collection):
    """$rename + $set on the same source path produces conflict (code 40)."""
    collection.insert_one({"_id": 1, "a": 10, "b": 20})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$rename": {"b": "z"}, "$set": {"b": 100}}}]},
    )
    assertFailureCode(result, 40)
