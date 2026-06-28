"""
Tests for update command bulk operations (multiple update statements).

Validates multiple update statements, mix of upsert/regular, and error handling.
"""

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command


def test_update_bulk_all_valid_statements(collection):
    """Test batch update with all valid statements returns correct n and nModified."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"x": 10}}},
                {"q": {"_id": 2}, "u": {"$set": {"x": 20}}},
                {"q": {"_id": 3}, "u": {"$set": {"x": 30}}},
            ],
        },
    )
    assertSuccess(result, {"ok": 1.0, "n": 3, "nModified": 3}, raw_res=True)


def test_update_bulk_same_query_upserts_then_updates(collection):
    """Test batch with same query twice: first upserts, second updates."""
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"x": 1}}, "upsert": True},
                {"q": {"_id": 1}, "u": {"$set": {"x": 2}}, "upsert": True},
            ],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0, "n": 2})


def test_update_bulk_mix_upsert_and_regular(collection):
    """Test mix of upsert and regular updates in same batch."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"x": 10}}},
                {"q": {"_id": 2}, "u": {"$set": {"x": 20}}, "upsert": True},
            ],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0, "n": 2})


def test_update_bulk_error_ordered_stops(collection):
    """Test batch with ordered:true stops at first DuplicateKey error."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}])
    collection.create_index("x", unique=True)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"x": 100}}},
                {"q": {"_id": 2}, "u": {"$set": {"x": 100}}},  # DuplicateKey
                {"q": {"_id": 1}, "u": {"$set": {"x": 200}}},
            ],
            "ordered": True,
        },
    )
    # First succeeds, second errors, third not executed
    assertSuccessPartial(result, {"ok": 1.0, "n": 1, "nModified": 1})


def test_update_bulk_error_unordered_continues(collection):
    """Test batch with ordered:false continues past errors."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}])
    collection.create_index("x", unique=True)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"x": 100}}},
                {"q": {"_id": 2}, "u": {"$set": {"x": 100}}},  # DuplicateKey
                {"q": {"_id": 3}, "u": {"$set": {"x": 300}}},
            ],
            "ordered": False,
        },
    )
    # First and third succeed, second errors
    assertSuccessPartial(result, {"ok": 1.0, "n": 2, "nModified": 2})
