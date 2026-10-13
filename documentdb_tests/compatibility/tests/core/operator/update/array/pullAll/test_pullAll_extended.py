"""
Extended tests for $pullAll update operator.

Covers removing all occurrences of values, type-sensitive matching, subdocument
matching, nested dotted paths, missing field (noop), empty value array (noop),
non-array operand error, non-array target field error, duplicates in value
array, multi:true, upsert:true, findAndModify post-image, composition with
$inc, same-path conflict with $set, and multiple fields in single $pullAll.

Oracle: MongoDB 7.0.
SUT-agnostic: assertions follow observed MongoDB behavior; engine divergences
are tracked via `engine_xfail` markers with tracking links.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.update


# ---- basic: removes all matching values --------------------------------------


def test_pullAll_removes_all_occurrences(collection):
    """$pullAll removes every occurrence of the specified value."""
    collection.insert_one({"_id": 1, "items": [1, 2, 1, 3, 1]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"items": [1]}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [2, 3]}])


# ---- type-sensitive: numeric types match across Int32/Int64 ------------------


def test_pullAll_numeric_type_matching(collection):
    """$pullAll with Int64(2) removes both int 2 and Int64(2) (numeric equivalence)."""
    collection.insert_one({"_id": 1, "items": [1, Int64(2), 3, Int64(4)]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pullAll": {"items": [Int64(2), 3]}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, Int64(4)]}])


# ---- subdocument matching (exact match) --------------------------------------


def test_pullAll_removes_matching_subdocuments(collection):
    """$pullAll with subdocument values removes exact-matching subdocuments."""
    collection.insert_one(
        {"_id": 1, "items": [{"a": 1}, {"a": 2}, {"a": 1}]}
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pullAll": {"items": [{"a": 1}]}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"a": 2}]}])


# ---- nested dotted path ------------------------------------------------------


def test_pullAll_on_nested_dotted_path(collection):
    """$pullAll works on a nested path specified with dot notation."""
    collection.insert_one({"_id": 1, "a": {"b": [1, 2, 3, 2]}})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"a.b": [2]}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"b": [1, 3]}}])


# ---- missing field is noop ---------------------------------------------------


def test_pullAll_on_missing_field_is_noop(collection):
    """$pullAll on a field that does not exist is a noop (nModified=0)."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"items": [1]}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- empty value array is noop -----------------------------------------------


def test_pullAll_with_empty_value_array_is_noop(collection):
    """$pullAll with an empty array of values to remove is a noop."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"items": []}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- duplicates in value array still remove all occurrences ------------------


def test_pullAll_duplicates_in_value_array(collection):
    """$pullAll with duplicates in the value array removes all occurrences."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3, 2, 1]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pullAll": {"items": [1, 1, 2]}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [3]}])


# ---- error: non-array operand ------------------------------------------------


def test_pullAll_non_array_operand_errors(collection):
    """$pullAll with a non-array operand (string) fails with code 2."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pullAll": {"items": "notarray"}}}
            ],
        },
    )
    assertFailureCode(result, 2)


# ---- error: target field is not an array -------------------------------------


def test_pullAll_on_non_array_target_errors(collection):
    """$pullAll on a field that is a string (not array) fails with code 2."""
    collection.insert_one({"_id": 1, "items": "hello"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pullAll": {"items": [1]}}}],
        },
    )
    assertFailureCode(result, 2)


# ---- multi: true -------------------------------------------------------------


def test_pullAll_multi_true_updates_all_matched(collection):
    """$pullAll with multi:true removes values from all matched documents."""
    collection.insert_many(
        [
            {"_id": 1, "items": [1, 2, 3]},
            {"_id": 2, "items": [2, 3, 4]},
            {"_id": 3, "items": [5, 6]},
        ]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {}, "u": {"$pullAll": {"items": [2, 3]}}, "multi": True}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "items": [1]},
            {"_id": 2, "items": [4]},
            {"_id": 3, "items": [5, 6]},
        ],
    )


# ---- upsert: true ------------------------------------------------------------


def test_pullAll_upsert_creates_document_without_field(collection):
    """$pullAll with upsert:true on missing doc creates doc without the array field."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 99}, "u": {"$pullAll": {"items": [1]}}, "upsert": True}
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}},
    )
    assertSuccess(result, [{"_id": 99}])


# ---- findAndModify -----------------------------------------------------------


def test_pullAll_find_and_modify_returns_post_image(collection):
    """$pullAll via findAndModify with new=true returns the updated document."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3, 2]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$pullAll": {"items": [2]}},
            "new": True,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": [1, 3]}})


# ---- composition: $pullAll + $inc on different paths -------------------------


def test_pullAll_composes_with_inc_on_different_path(collection):
    """$pullAll and $inc on different fields both apply cleanly."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3], "count": 10})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pullAll": {"items": [2]}, "$inc": {"count": -1}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 3], "count": 9}])


# ---- conflict: $pullAll + $set on same path ----------------------------------


def test_pullAll_conflicts_with_set_on_same_path(collection):
    """$pullAll and $set on the same path produces ConflictingUpdateOperators (code 40)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pullAll": {"items": [1]}, "$set": {"items": [99]}},
                }
            ],
        },
    )
    assertFailureCode(result, 40)


# ---- multiple fields in single $pullAll --------------------------------------


def test_pullAll_multiple_fields_simultaneously(collection):
    """$pullAll can target multiple array fields in a single operator expression."""
    collection.insert_one({"_id": 1, "a": [1, 2, 3], "b": [4, 5, 6]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pullAll": {"a": [2], "b": [4, 6]}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 3], "b": [5]}])
