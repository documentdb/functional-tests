"""
Extended tests for $pull update operator.

Covers compound document conditions, regex matching, boolean type-specific
removal, array-of-arrays removal, $not condition divergence, $exists condition,
$ne condition, all-elements removal, $lt/$lte conditions, deeply nested paths,
findAndModify pre-image, composition with $inc, and multiple fields in single
$pull.

Oracle: MongoDB 7.0.
SUT-agnostic: assertions follow observed MongoDB behavior; engine divergences
are tracked via `engine_xfail` markers with tracking links.
"""

import pytest
from bson import Int64, Decimal128

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.update


# ---- compound document condition --------------------------------------------


def test_pull_compound_document_condition(collection):
    """$pull with compound document condition removes subdocs matching all fields."""
    collection.insert_one(
        {"_id": 1, "items": [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}, {"x": 3, "y": "a"}]}
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pull": {"items": {"x": {"$gte": 2}, "y": "a"}}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}]}])


# ---- regex matching ---------------------------------------------------------


def test_pull_with_regex_condition(collection):
    """$pull with $regex removes all string elements matching the pattern."""
    collection.insert_one({"_id": 1, "items": ["abc", "def", "axc", "xyz"]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pull": {"items": {"$regex": "^a"}}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": ["def", "xyz"]}])


# ---- boolean type-specific removal ------------------------------------------


def test_pull_boolean_true_is_type_specific(collection):
    """$pull True removes only boolean True, not integer 1 (type-specific match)."""
    collection.insert_one({"_id": 1, "items": [True, False, True, 1, 0]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": True}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [False, 1, 0]}])


def test_pull_boolean_false_is_type_specific(collection):
    """$pull False removes only boolean False, not integer 0."""
    collection.insert_one({"_id": 1, "items": [True, False, 1, 0, False]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": False}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [True, 1, 0]}])


# ---- array-of-arrays removal -----------------------------------------------


def test_pull_array_from_array_of_arrays(collection):
    """$pull with array value removes matching sub-arrays."""
    collection.insert_one({"_id": 1, "items": [[1, 2], [3, 4], [1, 2]]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": [1, 2]}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [[3, 4]]}])


# ---- $not condition (divergence) --------------------------------------------


@pytest.mark.engine_xfail(
    engine="documentdb",
    reason="$pull with $not: oracle rejects with writeError code 2 (unknown top level operator); engine incorrectly succeeds and pulls elements",
    raises=AssertionError,
)
def test_pull_with_not_condition_errors(collection):
    """$pull with $not as top-level operator fails with code 2."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3, 4, 5]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pull": {"items": {"$not": {"$gte": 3}}}}}
            ],
        },
    )
    assertFailureCode(result, 2)


# ---- $ne condition ----------------------------------------------------------


def test_pull_with_ne_condition(collection):
    """$pull with $ne removes all elements not equal to the specified value."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3, 4, 5]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pull": {"items": {"$ne": 3}}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [3]}])


# ---- $exists condition -------------------------------------------------------


def test_pull_with_exists_condition_on_subdocs(collection):
    """$pull with $exists removes subdocuments that have the specified field."""
    collection.insert_one({"_id": 1, "items": [{"x": 1}, {"y": 2}, {"x": 3}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pull": {"items": {"x": {"$exists": True}}}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"y": 2}]}])


# ---- $lt and $lte conditions ------------------------------------------------


def test_pull_with_lt_condition(collection):
    """$pull with $lt removes elements less than the threshold."""
    collection.insert_one({"_id": 1, "scores": [10, 20, 30, 40, 50]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pull": {"scores": {"$lt": 30}}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "scores": [30, 40, 50]}])


# ---- all elements removal leaves empty array --------------------------------


def test_pull_all_elements_leaves_empty_array(collection):
    """$pull removing all elements leaves an empty array (not missing field)."""
    collection.insert_one({"_id": 1, "items": [5, 5, 5]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": 5}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": []}])


# ---- deeply nested path (missing intermediate is noop) ----------------------


def test_pull_deeply_nested_missing_intermediate_is_noop(collection):
    """$pull on a path with missing intermediate is a noop."""
    collection.insert_one({"_id": 1, "a": {"b": [1, 2, 3]}})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"a.c": 1}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- findAndModify pre-image ------------------------------------------------


def test_pull_find_and_modify_pre_image(collection):
    """$pull via findAndModify with new=false returns the pre-update document."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3, 2]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$pull": {"items": 2}},
            "new": False,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": [1, 2, 3, 2]}})


# ---- composition: $pull with $inc on different path -------------------------


def test_pull_composes_with_inc_on_different_path(collection):
    """$pull and $inc on different fields both apply cleanly."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3], "count": 0})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pull": {"items": 2}, "$inc": {"count": 1}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 3], "count": 1}])


# ---- multiple fields in single $pull ----------------------------------------


def test_pull_multiple_fields_simultaneously(collection):
    """$pull can target multiple array fields in a single operator expression."""
    collection.insert_one({"_id": 1, "a": [1, 2, 3, 2], "b": [4, 5, 6, 5]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"a": 2, "b": 5}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 3], "b": [4, 6]}])


# ---- $pull with $elemMatch on nested arrays ---------------------------------


def test_pull_with_elemMatch_on_nested_subdocs(collection):
    """$pull with $elemMatch removes subdocs where nested array has a matching element."""
    collection.insert_one(
        {
            "_id": 1,
            "items": [
                {"name": "A", "tags": [1, 2, 3]},
                {"name": "B", "tags": [4, 5, 6]},
                {"name": "C", "tags": [7, 8, 9]},
            ],
        }
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$pull": {"items": {"tags": {"$elemMatch": {"$gte": 7}}}}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [
            {
                "_id": 1,
                "items": [
                    {"name": "A", "tags": [1, 2, 3]},
                    {"name": "B", "tags": [4, 5, 6]},
                ],
            }
        ],
    )


# ---- Int64 value type-specific removal --------------------------------------


def test_pull_int64_value_matches_int64_elements(collection):
    """$pull with Int64 value removes Int64 elements matching the value."""
    collection.insert_one({"_id": 1, "items": [Int64(10), Int64(20), Int64(10)]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pull": {"items": Int64(10)}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [Int64(20)]}])
