"""
Extended tests for $push update operator.

Covers field creation on missing path, nested path creation, dotted-into-scalar
error, non-array target error, pushing various value types (subdocument, nested
array, null), empty array target, multi:true, upsert:true, findAndModify
post-image, composition with $inc, same-path conflict with $set, and array-of-
arrays.

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


# ---- field creation: missing field creates new array -------------------------


def test_push_creates_array_field_when_missing(collection):
    """$push on a missing field creates the field as a single-element array."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"items": "A"}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["A"]}])


# ---- field creation: nested dotted path creates intermediates ----------------


def test_push_nested_path_creates_intermediate_documents(collection):
    """$push on a dotted path with missing intermediates creates nested objects."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"a.b.c": 1}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"b": {"c": [1]}}}])


# ---- error: dotted path into scalar (PathNotViable) --------------------------


def test_push_dotted_into_scalar_errors(collection):
    """$push on a path that traverses a scalar field fails with code 28."""
    collection.insert_one({"_id": 1, "a": 5})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"a.b": 1}}}],
        },
    )
    assertFailureCode(result, 28)


# ---- error: target is not an array (string) ----------------------------------


def test_push_on_string_field_errors(collection):
    """$push on a field that is a string fails with code 2."""
    collection.insert_one({"_id": 1, "x": "hello"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"x": 1}}}],
        },
    )
    assertFailureCode(result, 2)


# ---- error: target is not an array (subdocument) -----------------------------


def test_push_on_subdocument_field_errors(collection):
    """$push on a field that is a subdocument fails with code 2."""
    collection.insert_one({"_id": 1, "items": {"a": 1}})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"items": 1}}}],
        },
    )
    assertFailureCode(result, 2)


# ---- pushing various value types ---------------------------------------------


def test_push_subdocument_into_array(collection):
    """$push can append a subdocument as an array element."""
    collection.insert_one({"_id": 1, "items": [{"a": 1}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$push": {"items": {"a": 2, "b": "hi"}}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"a": 1}, {"a": 2, "b": "hi"}]}])


def test_push_nested_array_into_array(collection):
    """$push can append an array as an element (array-of-arrays)."""
    collection.insert_one({"_id": 1, "items": [1, 2]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"items": [3, 4]}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 2, [3, 4]]}])


def test_push_null_value(collection):
    """$push can append null as an array element."""
    collection.insert_one({"_id": 1, "items": [1]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"items": None}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, None]}])


# ---- push to empty array -----------------------------------------------------


def test_push_to_empty_array(collection):
    """$push on an empty array adds the element as the sole member."""
    collection.insert_one({"_id": 1, "items": []})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$push": {"items": "first"}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["first"]}])


# ---- multi: true -------------------------------------------------------------


def test_push_multi_true_updates_all_matched(collection):
    """$push with multi:true appends to all matched documents."""
    collection.insert_many(
        [{"_id": 1, "items": [1]}, {"_id": 2, "items": [2]}, {"_id": 3, "items": [3]}]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$push": {"items": 99}}, "multi": True}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "items": [1, 99]},
            {"_id": 2, "items": [2, 99]},
            {"_id": 3, "items": [3, 99]},
        ],
    )


# ---- upsert: true ------------------------------------------------------------


def test_push_upsert_creates_document_with_array(collection):
    """$push with upsert:true on a non-existent doc creates it with the array."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 99}, "u": {"$push": {"items": "X"}}, "upsert": True}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 99, "items": ["X"]}])


# ---- findAndModify -----------------------------------------------------------


def test_push_find_and_modify_returns_post_image(collection):
    """$push via findAndModify with new=true returns the updated document."""
    collection.insert_one({"_id": 1, "items": [1, 2]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$push": {"items": 3}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": [1, 2, 3]}})


# ---- composition: $push + $inc on different paths ----------------------------


def test_push_composes_with_inc_on_different_path(collection):
    """$push and $inc on different fields both apply cleanly."""
    collection.insert_one({"_id": 1, "items": [1], "count": 0})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$push": {"items": 2}, "$inc": {"count": 1}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 2], "count": 1}])


# ---- conflict: $push + $set on same path ------------------------------------


def test_push_conflicts_with_set_on_same_path(collection):
    """$push and $set on the same path produces ConflictingUpdateOperators (code 40)."""
    collection.insert_one({"_id": 1, "items": [1]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$push": {"items": 2}, "$set": {"items": [99]}},
                }
            ],
        },
    )
    assertFailureCode(result, 40)


# ---- multiple fields in single $push ----------------------------------------


def test_push_multiple_fields_simultaneously(collection):
    """$push can target multiple array fields in a single operator expression."""
    collection.insert_one({"_id": 1, "a": [1], "b": [10]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$push": {"a": 2, "b": 20}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 2], "b": [10, 20]}])
