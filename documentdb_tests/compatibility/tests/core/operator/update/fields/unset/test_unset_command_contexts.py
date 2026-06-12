"""
Tests for $unset update operator - command contexts.

Covers updateOne, updateMany, upsert, and nModified wiring.
"""

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command


def test_unset_upsert_no_match(collection):
    """Test upsert with $unset on non-existent doc creates doc without field."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {"missing": ""}}, "upsert": True}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1}], msg="Upsert with $unset should create doc without field")


def test_unset_update_one(collection):
    """Test $unset in updateOne removes field from one doc."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1, "b": 2}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"a": 1}, "u": {"$unset": {"b": ""}}}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 1, "ok": 1.0}, msg="Should unset in one doc")


def test_unset_nmodified_zero_when_field_missing(collection):
    """Test $unset on non-existent field returns nModified: 0."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {"missing": ""}}}],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="Unset non-existent field should have nModified: 0",
    )


def test_unset_update_many(collection):
    """Test $unset in updateMany removes field from all matching."""
    collection.insert_many([{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1, "b": 3}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"a": 1}, "u": {"$unset": {"b": ""}}, "multi": True}],
        },
    )
    assertSuccessPartial(
        result, {"n": 2, "nModified": 2, "ok": 1.0}, msg="Should unset from all matching"
    )
