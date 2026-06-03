"""
Comprehensive tests for $pull update operator.

Covers exact value removal, conditional removal ($gte, $in, doc-match),
empty arrays, missing fields, non-array errors, nested paths,
command paths (update, findAndModify), multi-document updates, upsert,
and composition.

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


# ---- happy path: exact value -------------------------------------------------


def test_pull_removes_all_matching_values(collection):
    """$pull removes all occurrences of the specified value."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3, 2, 4]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": 2}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 3, 4]}])


def test_pull_noop_when_value_not_found(collection):
    """$pull is a no-op when the value is not in the array."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": 99}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_pull_empty_array_is_noop(collection):
    """$pull on empty array is a no-op."""
    collection.insert_one({"_id": 1, "items": []})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": 1}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_pull_missing_field_is_noop(collection):
    """$pull on a missing field is a no-op."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": 1}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- conditional pull --------------------------------------------------------


def test_pull_with_gte_condition(collection):
    """$pull with $gte removes all elements >= threshold."""
    collection.insert_one({"_id": 1, "items": [1, 5, 10, 15, 20]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": {"$gte": 10}}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 5]}])


def test_pull_with_in_condition(collection):
    """$pull with $in removes elements matching any value in the list."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3, 4, 5]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": {"$in": [2, 4]}}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 3, 5]}])


def test_pull_document_match(collection):
    """$pull with document condition removes matching subdocuments."""
    collection.insert_one({"_id": 1, "items": [{"a": 1}, {"a": 2}, {"a": 3}]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": {"a": 2}}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"a": 1}, {"a": 3}]}])


def test_pull_document_with_multiple_fields(collection):
    """$pull matches subdocuments where all specified fields match."""
    collection.insert_one({"_id": 1, "items": [
        {"x": 1, "y": "a"},
        {"x": 2, "y": "b"},
        {"x": 1, "y": "c"},
    ]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": {"x": 1, "y": "a"}}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"x": 2, "y": "b"}, {"x": 1, "y": "c"}]}])


# ---- path semantics ----------------------------------------------------------


def test_pull_nested_path(collection):
    """$pull works on nested dotted paths."""
    collection.insert_one({"_id": 1, "a": {"items": [1, 2, 3, 2]}})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"a.items": 2}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"items": [1, 3]}}])


# ---- command paths -----------------------------------------------------------


def test_pull_via_find_and_modify(collection):
    """$pull works via findAndModify, returns new document."""
    collection.insert_one({"_id": 1, "items": ["a", "b", "c"]})
    result = execute_command(
        collection,
        {"findAndModify": collection.name, "query": {"_id": 1}, "update": {"$pull": {"items": "b"}}, "new": True},
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": ["a", "c"]}})


def test_pull_multi_true(collection):
    """$pull with multi:true removes from all matched documents."""
    collection.insert_many([
        {"_id": 1, "items": [1, 2, 3]},
        {"_id": 2, "items": [2, 3, 4]},
        {"_id": 3, "items": [5, 6, 7]},
    ])
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$pull": {"items": 2}}, "multi": True}]},
    )
    assertSuccessPartial(result, {"n": 3, "nModified": 2, "ok": 1.0})


def test_pull_upsert_creates_doc_without_pulled_field(collection):
    """$pull with upsert:true creates a document without the field."""
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 99}, "u": {"$pull": {"items": 1}}, "upsert": True}]},
    )
    doc = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}}
    )
    assertSuccess(doc, [{"_id": 99}])


# ---- composition -------------------------------------------------------------


def test_pull_composes_with_set_on_different_path(collection):
    """$pull composes with $set on a different field."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3], "x": "old"})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": 2}, "$set": {"x": "new"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 3], "x": "new"}])


# ---- error cases -------------------------------------------------------------


def test_pull_non_array_field_fails(collection):
    """$pull on a non-array field fails with BadValue (code 2)."""
    collection.insert_one({"_id": 1, "items": "not_array"})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": 1}}}]},
    )
    assertFailureCode(result, 2)


def test_pull_conflicts_with_push_on_same_path(collection):
    """$pull and $push on the same path produces ConflictingUpdateOperators."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": 1}, "$push": {"items": 4}}}]},
    )
    assertFailureCode(result, 40)
