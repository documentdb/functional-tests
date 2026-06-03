"""
Comprehensive tests for $pop update operator.

Covers pop-last, pop-first, empty arrays, missing fields, non-array errors,
invalid values, nested paths, command paths (update, findAndModify),
multi-document updates, upsert, and composition.

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


# ---- happy path: basic pop ---------------------------------------------------


def test_pop_last_element(collection):
    """$pop with 1 removes the last array element."""
    collection.insert_one({"_id": 1, "items": ["A", "B", "C"]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A", "B"]}])


def test_pop_first_element(collection):
    """$pop with -1 removes the first array element."""
    collection.insert_one({"_id": 1, "items": ["A", "B", "C"]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": -1}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["B", "C"]}])


def test_pop_single_element_array(collection):
    """$pop on single-element array leaves empty array."""
    collection.insert_one({"_id": 1, "items": ["only"]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": []}])


def test_pop_empty_array_is_noop(collection):
    """$pop on empty array is a no-op (nModified=0)."""
    collection.insert_one({"_id": 1, "items": []})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_pop_missing_field_is_noop(collection):
    """$pop on a missing field is a no-op."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- path semantics ----------------------------------------------------------


def test_pop_nested_path(collection):
    """$pop works on nested dotted paths."""
    collection.insert_one({"_id": 1, "a": {"items": ["x", "y", "z"]}})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"a.items": 1}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"items": ["x", "y"]}}])


# ---- command paths -----------------------------------------------------------


def test_pop_via_find_and_modify(collection):
    """$pop works via findAndModify, returns new document."""
    collection.insert_one({"_id": 1, "items": [10, 20, 30]})
    result = execute_command(
        collection,
        {"findAndModify": collection.name, "query": {"_id": 1}, "update": {"$pop": {"items": -1}}, "new": True},
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": [20, 30]}})


def test_pop_multi_true(collection):
    """$pop with multi:true pops from all matched documents."""
    collection.insert_many([
        {"_id": 1, "items": [1, 2, 3]},
        {"_id": 2, "items": [4, 5, 6]},
    ])
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$pop": {"items": 1}}, "multi": True}]},
    )
    assertSuccessPartial(result, {"n": 2, "nModified": 2, "ok": 1.0})


def test_pop_upsert_creates_empty_doc(collection):
    """$pop with upsert:true creates a document without the popped field."""
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 99}, "u": {"$pop": {"items": 1}}, "upsert": True}]},
    )
    doc = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}}
    )
    assertSuccess(doc, [{"_id": 99}])


# ---- composition -------------------------------------------------------------


def test_pop_composes_with_set_on_different_path(collection):
    """$pop composes with $set on a different field."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3], "x": "old"})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}, "$set": {"x": "new"}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 2], "x": "new"}])


# ---- error cases -------------------------------------------------------------


@pytest.mark.engine_xfail(
    engine="pgmongo",
    reason="returns error code 2 (BadValue) instead of 14 (TypeMismatch) for non-array field",
    raises=AssertionError,
)
def test_pop_non_array_field_fails(collection):
    """$pop on a non-array field fails with TypeMismatch (code 14)."""
    collection.insert_one({"_id": 1, "items": "not_array"})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}]},
    )
    assertFailureCode(result, 14)


def test_pop_invalid_value_zero_fails(collection):
    """$pop with value 0 fails with FailedToParse (code 9)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 0}}}]},
    )
    assertFailureCode(result, 9)


def test_pop_conflicts_with_pull_on_same_path(collection):
    """$pop and $pull on the same path produces ConflictingUpdateOperators."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}, "$pull": {"items": 2}}}]},
    )
    assertFailureCode(result, 40)
