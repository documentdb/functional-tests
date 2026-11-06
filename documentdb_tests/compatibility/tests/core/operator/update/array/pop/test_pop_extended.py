"""
Extended tests for $pop update operator.

Covers value boundary cases (0, values > 1, values < -1, float 1.5, boolean),
Int64 typed value, array-of-arrays, deeply nested missing path, multiple
fields in single $pop, findAndModify pre-image, and additional composition
with $inc.

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


# ---- value boundary: 0 (error) -----------------------------------------------


def test_pop_value_zero_errors(collection):
    """$pop with value 0 fails — only 1 or -1 are valid (code 9)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 0}}}],
        },
    )
    assertFailureCode(result, 9)


# ---- value boundary: positive > 1 (error) -----------------------------------


def test_pop_value_greater_than_one_errors(collection):
    """$pop with value > 1 (e.g. 2) fails — only exactly 1 pops from end (code 9)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 2}}}],
        },
    )
    assertFailureCode(result, 9)


# ---- value boundary: negative < -1 (error) ----------------------------------


def test_pop_value_less_than_neg_one_errors(collection):
    """$pop with value < -1 (e.g. -5) fails — only exactly -1 pops from front (code 9)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": -5}}}],
        },
    )
    assertFailureCode(result, 9)


# ---- value boundary: float 1.0 pops from end --------------------------------


def test_pop_float_one_pops_last(collection):
    """$pop with float 1.0 is equivalent to integer 1 — pops last element."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1.0}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 2]}])


# ---- value boundary: float -1.0 pops from front -----------------------------


def test_pop_float_neg_one_pops_first(collection):
    """$pop with float -1.0 is equivalent to integer -1 — pops first element."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": -1.0}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [2, 3]}])


# ---- value boundary: float 1.5 is error (not exactly 1 or -1) ---------------


def test_pop_float_one_point_five_errors(collection):
    """$pop with value 1.5 fails — only exactly 1 or -1 trigger a pop (code 9)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1.5}}}],
        },
    )
    assertFailureCode(result, 9)


# ---- value boundary: boolean errors ------------------------------------------


def test_pop_boolean_value_errors(collection):
    """$pop with boolean True fails — expected a number (code 9)."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": True}}}],
        },
    )
    assertFailureCode(result, 9)


# ---- Int64 typed value -------------------------------------------------------


def test_pop_int64_one_pops_last(collection):
    """$pop with Int64(1) is equivalent to integer 1 — pops last element."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": Int64(1)}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [1, 2]}])


def test_pop_int64_neg_one_pops_first(collection):
    """$pop with Int64(-1) is equivalent to integer -1 — pops first element."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": Int64(-1)}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [2, 3]}])


# ---- array-of-arrays --------------------------------------------------------


def test_pop_on_array_of_arrays(collection):
    """$pop removes the last sub-array from an array of arrays."""
    collection.insert_one({"_id": 1, "items": [[1, 2], [3, 4], [5, 6]]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [[1, 2], [3, 4]]}])


# ---- deeply nested missing path (noop) --------------------------------------


def test_pop_deeply_nested_missing_path_is_noop(collection):
    """$pop on a deeply nested path with missing intermediates is a noop."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"a.b.c": 1}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- multiple fields in single $pop -----------------------------------------


def test_pop_multiple_fields_simultaneously(collection):
    """$pop can target multiple array fields in a single operator expression."""
    collection.insert_one({"_id": 1, "a": [1, 2, 3], "b": [4, 5, 6]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"a": 1, "b": -1}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 2], "b": [5, 6]}])


# ---- findAndModify pre-image ------------------------------------------------


def test_pop_find_and_modify_pre_image(collection):
    """$pop via findAndModify with new=false returns the pre-update document."""
    collection.insert_one({"_id": 1, "items": [10, 20, 30]})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$pop": {"items": 1}},
            "new": False,
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "items": [10, 20, 30]}})


# ---- composition: $pop with $inc --------------------------------------------


def test_pop_composes_with_inc_on_different_path(collection):
    """$pop and $inc on different fields both apply cleanly."""
    collection.insert_one({"_id": 1, "items": [1, 2, 3], "count": 10})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$pop": {"items": -1}, "$inc": {"count": 1}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": [2, 3], "count": 11}])


# ---- repeated pops drain the array ------------------------------------------


def test_pop_repeated_drains_to_empty(collection):
    """Repeated $pop operations drain the array to empty."""
    collection.insert_one({"_id": 1, "items": [1, 2]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}],
        },
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$pop": {"items": 1}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "items": []}])
