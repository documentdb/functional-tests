"""
Tests for cross-operator interactions at the update/fields level.

Covers meaningful interactions between field update operators (same-path conflicts).
"""

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import CONFLICTING_UPDATE_OPERATORS_ERROR
from documentdb_tests.framework.executor import execute_command


def test_set_inc_same_path_conflict(collection):
    """$set and $inc on the same field should produce a conflict error."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}, "$inc": {"a": 1}}}],
        },
    )
    assertFailureCode(
        result, CONFLICTING_UPDATE_OPERATORS_ERROR, msg="Same-path $set + $inc should conflict"
    )
