"""
Extended tests for $[<identifier>] (positional filtered) update operator.

Covers additional operator combinations ($unset, $mul), arrayFilter with $regex,
batch updates with different arrayFilters per statement, scalar field target (noop),
identifier validation errors, type matrix for arrayFilter conditions, and
path semantics (dotted into nested arrays by index).

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


# ---- operator combinations --------------------------------------------------


def test_positional_filtered_unset_matching_elements(collection):
    """$[<identifier>] with $unset removes fields from matching array elements."""
    collection.insert_one(
        {"_id": 1, "items": [{"x": 1, "y": "a"}, {"x": 2, "y": "b"}, {"x": 3, "y": "c"}]}
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$unset": {"items.$[elem].y": 1}},
                    "arrayFilters": [{"elem.x": {"$gte": 2}}],
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result,
        [{"_id": 1, "items": [{"x": 1, "y": "a"}, {"x": 2}, {"x": 3}]}],
    )


def test_positional_filtered_mul_matching_elements(collection):
    """$[<identifier>] with $mul multiplies only matching array element fields."""
    collection.insert_one({"_id": 1, "items": [{"v": 2}, {"v": 5}, {"v": 10}]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$mul": {"items.$[elem].v": 3}},
                    "arrayFilters": [{"elem.v": {"$gte": 5}}],
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"v": 2}, {"v": 15}, {"v": 30}]}])


# ---- arrayFilter with $regex ------------------------------------------------


def test_positional_filtered_arrayfilter_with_regex(collection):
    """$[<identifier>] arrayFilter supports $regex for string matching."""
    collection.insert_one(
        {"_id": 1, "items": [{"name": "abc"}, {"name": "def"}, {"name": "axc"}]}
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].matched": True}},
                    "arrayFilters": [{"elem.name": {"$regex": "^a"}}],
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
                    {"name": "abc", "matched": True},
                    {"name": "def"},
                    {"name": "axc", "matched": True},
                ],
            }
        ],
    )


# ---- batch updates with different arrayFilters per statement ----------------


def test_positional_filtered_batch_updates_different_filters(collection):
    """Multiple update statements with different arrayFilters apply independently."""
    collection.insert_one({"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"a.$[x]": 0}},
                    "arrayFilters": [{"x": {"$gte": 2}}],
                },
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"b.$[y]": 0}},
                    "arrayFilters": [{"y": {"$lte": 10}}],
                },
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 0, 0], "b": [0, 20, 30]}])


# ---- scalar field target (error) --------------------------------------------


@pytest.mark.engine_xfail(
    engine="documentdb",
    reason="Returns error code 28 (PathNotViable) instead of code 2 for array update on non-array field",
    raises=AssertionError,
)
def test_positional_filtered_on_scalar_field_errors(collection):
    """$[<identifier>] targeting a scalar field fails with code 2."""
    collection.insert_one({"_id": 1, "items": "scalar_value"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem]": 99}},
                    "arrayFilters": [{"elem": {"$gte": 0}}],
                }
            ],
        },
    )
    assertFailureCode(result, 2)


# ---- arrayFilter with numeric type conditions -------------------------------


def test_positional_filtered_arrayfilter_int64_threshold(collection):
    """$[<identifier>] arrayFilter correctly handles Int64 threshold comparison."""
    collection.insert_one(
        {"_id": 1, "items": [{"v": Int64(100)}, {"v": Int64(200)}, {"v": Int64(300)}]}
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].v": Int64(0)}},
                    "arrayFilters": [{"elem.v": {"$gte": Int64(200)}}],
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(
        result, [{"_id": 1, "items": [{"v": Int64(100)}, {"v": Int64(0)}, {"v": Int64(0)}]}]
    )


# ---- path semantics: dotted into array by index -----------------------------


def test_positional_filtered_dotted_index_into_nested_array(collection):
    """$[<identifier>] with dotted path reaching into nested subdocument arrays."""
    collection.insert_one(
        {
            "_id": 1,
            "matrix": [
                {"row": "A", "vals": [1, 2, 3]},
                {"row": "B", "vals": [4, 5, 6]},
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
                    "u": {"$set": {"matrix.$[r].vals.0": 99}},
                    "arrayFilters": [{"r.row": "B"}],
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
                "matrix": [
                    {"row": "A", "vals": [1, 2, 3]},
                    {"row": "B", "vals": [99, 5, 6]},
                ],
            }
        ],
    )


# ---- findAndModify returning pre-image (new=false) --------------------------


def test_positional_filtered_find_and_modify_pre_image(collection):
    """$[<identifier>] via findAndModify with new=false returns the pre-update doc."""
    collection.insert_one({"_id": 1, "items": [{"x": 1}, {"x": 5}, {"x": 10}]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"items.$[elem].x": 0}},
            "arrayFilters": [{"elem.x": {"$gte": 5}}],
            "new": False,
        },
    )
    assertSuccessPartial(
        result, {"value": {"_id": 1, "items": [{"x": 1}, {"x": 5}, {"x": 10}]}}
    )


# ---- composition: $[<identifier>] with $inc on different paths ---------------


def test_positional_filtered_composes_with_inc_on_different_path(collection):
    """$[<identifier>] $set and $inc on a separate top-level field both apply."""
    collection.insert_one({"_id": 1, "items": [{"v": 5}, {"v": 15}], "count": 0})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem].v": 0}, "$inc": {"count": 1}},
                    "arrayFilters": [{"elem.v": {"$gte": 10}}],
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [{"v": 5}, {"v": 0}], "count": 1}])


# ---- error cases (extended) -------------------------------------------------


@pytest.mark.engine_xfail(
    engine="documentdb",
    reason="Accepts identifier starting with digit instead of rejecting with writeError code 2",
    raises=AssertionError,
)
def test_positional_filtered_identifier_starting_with_digit_errors(collection):
    """arrayFilter identifier starting with a digit fails with code 2."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[0bad]": 99}},
                    "arrayFilters": [{"0bad": {"$gte": 2}}],
                }
            ],
        },
    )
    assertFailureCode(result, 2)


def test_positional_filtered_extra_unused_arrayfilter_errors(collection):
    """An arrayFilter entry not referenced in the update path fails with code 9."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem]": 0}},
                    "arrayFilters": [{"elem": {"$gte": 2}}, {"unused": {"$lte": 5}}],
                }
            ],
        },
    )
    assertFailureCode(result, 9)


def test_positional_filtered_empty_arrayfilters_list_with_identifier_errors(collection):
    """$[<identifier>] with empty arrayFilters list fails with code 2."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"items.$[elem]": 0}},
                    "arrayFilters": [],
                }
            ],
        },
    )
    assertFailureCode(result, 2)
