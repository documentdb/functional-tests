"""
Tests for update command hint option.

Validates hint with document spec, string name, and error for non-existent index.
"""

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command


def test_update_hint_with_index_spec(collection):
    """Test hint as document {field: 1} uses index."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}])
    collection.create_index("x")
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"x": 1}, "u": {"$set": {"y": 1}}, "hint": {"x": 1}}],
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 1, "nModified": 1}, raw_res=True)


def test_update_hint_with_index_name(collection):
    """Test hint as string uses named index."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}])
    collection.create_index("x", name="x_idx")
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"x": 1}, "u": {"$set": {"y": 1}}, "hint": "x_idx"}],
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 1, "nModified": 1}, raw_res=True)


def test_update_hint_non_existent_index_errors(collection):
    """Test hint with non-existent index errors."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"x": 1}, "u": {"$set": {"y": 1}}, "hint": {"z": 1}}],
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR)
