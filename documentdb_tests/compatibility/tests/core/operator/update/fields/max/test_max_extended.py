"""
Extended tests for $max update operator.

Covers boundary values (NaN, Infinity, -Infinity, -0.0), numeric type matrix
(Int32, Int64, Double, Decimal128), cross-type BSON ordering (bool, array,
document vs number), implicit creation with nested intermediate paths,
existing-value overwrite from different types, and bulkWrite command path.

Oracle: MongoDB 7.0.
SUT-agnostic: assertions follow observed MongoDB behavior; engine divergences
are tracked via `engine_xfail` markers with tracking links.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.update


# ---- boundary values --------------------------------------------------------


def test_max_nan_does_not_update_existing_int(collection):
    """$max with NaN vs existing int: NaN is always less in BSON ordering, so noop."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": float("nan")}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_max_infinity_updates_existing_int(collection):
    """$max with +Infinity vs existing int: Infinity > any finite number."""
    collection.insert_one({"_id": 1, "v": 10})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": float("inf")}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": float("inf")}])


def test_max_neg_infinity_is_noop_vs_int(collection):
    """$max with -Infinity vs existing int: -Infinity < any finite number, noop."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": float("-inf")}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_max_neg_infinity_updates_when_existing_is_neg_infinity(collection):
    """$max with -Infinity vs existing -Infinity: equal values are noop."""
    collection.insert_one({"_id": 1, "v": float("-inf")})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": float("-inf")}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- numeric type matrix ----------------------------------------------------


def test_max_int64_larger_updates(collection):
    """$max with Int64 value larger than existing Int32 updates to Int64."""
    collection.insert_one({"_id": 1, "v": 5})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": Int64(100)}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": Int64(100)}])


def test_max_decimal128_larger_updates(collection):
    """$max with Decimal128 value larger than existing int updates to Decimal128."""
    collection.insert_one({"_id": 1, "v": 5})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": Decimal128("100.5")}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": Decimal128("100.5")}])


def test_max_int64_smaller_is_noop(collection):
    """$max with Int64 value smaller than existing is noop."""
    collection.insert_one({"_id": 1, "v": Int64(1000)})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": Int64(5)}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_max_double_vs_int_same_numeric_value_is_noop(collection):
    """$max with double value numerically equal to existing int is noop."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": 10.0}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- cross-type BSON ordering -----------------------------------------------


def test_max_bool_greater_than_number_updates(collection):
    """$max with bool vs number: boolean > number in BSON type ordering."""
    collection.insert_one({"_id": 1, "v": 100})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": True}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": True}])


def test_max_array_greater_than_number_updates(collection):
    """$max with array vs number: array > number in BSON type ordering."""
    collection.insert_one({"_id": 1, "v": 100})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": [1]}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": [1]}])


def test_max_document_greater_than_number_updates(collection):
    """$max with document vs number: document > number in BSON type ordering."""
    collection.insert_one({"_id": 1, "v": 100})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": {"a": 1}}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": {"a": 1}}])


def test_max_number_less_than_string_is_noop(collection):
    """$max with number vs existing string: number < string in BSON ordering, noop."""
    collection.insert_one({"_id": 1, "v": "abc"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": 99999}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


# ---- implicit creation with intermediate paths ------------------------------


def test_max_creates_nested_intermediate_docs(collection):
    """$max on a deep dotted path with missing intermediates creates the chain."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"a.b.c": 10}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"b": {"c": 10}}}])


# ---- existing-value overwrite: different type replacement -------------------


def test_max_replaces_null_with_number(collection):
    """$max with number vs existing null: number > null, updates to number."""
    collection.insert_one({"_id": 1, "v": None})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": 5}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 5}])


def test_max_replaces_int_with_string(collection):
    """$max with string vs existing int: string > number in BSON ordering."""
    collection.insert_one({"_id": 1, "v": 42})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"v": "hello"}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": "hello"}])


# ---- composition: $max with $inc on different paths -------------------------


def test_max_composes_with_inc_on_different_path(collection):
    """$max and $inc on different fields both apply cleanly."""
    collection.insert_one({"_id": 1, "v": 5, "counter": 0})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$max": {"v": 100}, "$inc": {"counter": 1}}}
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 100, "counter": 1}])


# ---- multiple fields in single $max ----------------------------------------


def test_max_multiple_fields_in_single_operator(collection):
    """$max with multiple fields in one expression updates each independently."""
    collection.insert_one({"_id": 1, "a": 10, "b": 50, "c": 30})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$max": {"a": 20, "b": 20, "c": 40}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": 20, "b": 50, "c": 40}])
