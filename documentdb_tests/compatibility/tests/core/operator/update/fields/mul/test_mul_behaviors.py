"""
Comprehensive tests for $mul update operator.

Covers type coercion, missing fields, boundary values, nested paths,
command paths (update, findAndModify), multi-document updates, upsert,
composition, and error cases.

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


# ---- happy path: type matrix ------------------------------------------------


def test_mul_int32_times_int32(collection):
    """$mul with int32 * int32 produces int32 result."""
    collection.insert_one({"_id": 1, "v": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 3}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 30}])


def test_mul_int64_times_int64(collection):
    """$mul with Int64 * Int64 produces Int64 result."""
    collection.insert_one({"_id": 1, "v": Int64(100)})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": Int64(3)}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": Int64(300)}])


def test_mul_double_times_double(collection):
    """$mul with double * double produces double result."""
    collection.insert_one({"_id": 1, "v": 2.5})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 2.0}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 5.0}])


def test_mul_int64_times_double_promotes_to_double(collection):
    """$mul with Int64 * double promotes result to double."""
    collection.insert_one({"_id": 1, "v": Int64(10)})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 2.5}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 25.0}])


def test_mul_int32_times_int64_promotes_to_int64(collection):
    """$mul with int32 * Int64 promotes result to Int64."""
    collection.insert_one({"_id": 1, "v": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": Int64(3)}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": Int64(30)}])


def test_mul_decimal128_times_int(collection):
    """$mul with Decimal128 * int produces Decimal128 result."""
    collection.insert_one({"_id": 1, "v": Decimal128("10.5")})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 2}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": Decimal128("21.0")}])


# ---- boundary values ---------------------------------------------------------


def test_mul_by_zero_returns_zero(collection):
    """$mul by 0 sets the field to 0."""
    collection.insert_one({"_id": 1, "v": 42})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 0}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 0}])


def test_mul_by_one_is_noop(collection):
    """$mul by 1 does not modify the value (nModified=0)."""
    collection.insert_one({"_id": 1, "v": 7})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 1}}}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_mul_negative_multiplier(collection):
    """$mul with a negative multiplier negates the value."""
    collection.insert_one({"_id": 1, "v": 10})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": -3}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": -30}])


# ---- missing field and implicit creation -------------------------------------


def test_mul_on_missing_field_creates_zero(collection):
    """$mul on a missing field creates it with value 0."""
    collection.insert_one({"_id": 1, "other": "x"})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 3}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "other": "x", "v": 0}])


def test_mul_on_missing_field_int64_creates_int64_zero(collection):
    """$mul missing field with Int64 multiplier creates Int64(0)."""
    collection.insert_one({"_id": 1, "other": "x"})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": Int64(5)}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "other": "x", "v": Int64(0)}])


# ---- nested path -------------------------------------------------------------


def test_mul_nested_dotted_path(collection):
    """$mul works on dotted nested paths."""
    collection.insert_one({"_id": 1, "a": {"b": 5}})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"a.b": 3}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "a": {"b": 15}}])


# ---- command paths -----------------------------------------------------------


def test_mul_via_find_and_modify(collection):
    """$mul works through findAndModify and returns the updated document."""
    collection.insert_one({"_id": 1, "v": 7})
    result = execute_command(
        collection,
        {"findAndModify": collection.name, "query": {"_id": 1}, "update": {"$mul": {"v": 3}}, "new": True},
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "v": 21}})


# ---- multi and upsert --------------------------------------------------------


def test_mul_multi_true_updates_all_matched(collection):
    """$mul with multi:true multiplies across all matched documents."""
    collection.insert_many([{"_id": i, "v": i * 10} for i in range(1, 4)])
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$mul": {"v": 2}}, "multi": True}]},
    )
    assertSuccessPartial(result, {"n": 3, "nModified": 3, "ok": 1.0})


def test_mul_multi_true_result_values(collection):
    """$mul with multi:true produces correct values in all docs."""
    collection.insert_many([{"_id": 1, "v": 10}, {"_id": 2, "v": 20}, {"_id": 3, "v": 30}])
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {}, "u": {"$mul": {"v": 2}}, "multi": True}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 20}, {"_id": 2, "v": 40}, {"_id": 3, "v": 60}])


def test_mul_upsert_creates_doc_with_zero(collection):
    """$mul with upsert on non-existing doc creates it with the field set to 0."""
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 99}, "u": {"$mul": {"v": 5}}, "upsert": True}]},
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 0, "ok": 1.0})


def test_mul_upsert_doc_value(collection):
    """$mul with upsert produces a document with field value 0."""
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 99}, "u": {"$mul": {"v": 5}}, "upsert": True}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 99}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 99, "v": 0}])


# ---- composition -------------------------------------------------------------


def test_mul_composes_with_set_on_different_paths(collection):
    """$mul and $set on different fields both apply cleanly."""
    collection.insert_one({"_id": 1, "v": 5, "name": "old"})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 3}, "$set": {"name": "new"}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "sort": {"_id": 1}}
    )
    assertSuccess(result, [{"_id": 1, "v": 15, "name": "new"}])


# ---- error cases -------------------------------------------------------------


def test_mul_rejects_string_multiplier(collection):
    """$mul with a non-numeric multiplier fails with code 14 (TypeMismatch)."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": "abc"}}}]},
    )
    assertFailureCode(result, 14)


def test_mul_rejects_non_numeric_field_value(collection):
    """$mul on a field with a non-numeric value fails with code 14."""
    collection.insert_one({"_id": 1, "v": "hello"})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 2}}}]},
    )
    assertFailureCode(result, 14)


def test_mul_conflicts_with_set_on_same_path(collection):
    """$mul + $set on the same path produces ConflictingUpdateOperators (code 40)."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$mul": {"v": 2}, "$set": {"v": 100}}}]},
    )
    assertFailureCode(result, 40)
