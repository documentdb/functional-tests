"""
Tests for update command ordered vs unordered execution.

Validates that ordered:true stops on first error and ordered:false
continues executing all statements.
"""

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command


def test_update_ordered_true_stops_at_first_error(collection):
    """Test ordered:true stops execution at first error."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"x": 10}}},
                {"q": {"_id": 2}, "u": {"$set": {"_id": 999}}},  # error: can't modify _id
                {"q": {"_id": 3}, "u": {"$set": {"x": 30}}},
            ],
            "ordered": True,
        },
    )
    # First succeeds, second errors, third NOT executed
    assertSuccessPartial(result, {"ok": 1.0, "n": 1, "nModified": 1})


def test_update_ordered_false_continues_past_errors(collection):
    """Test ordered:false continues executing all statements past errors."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"x": 10}}},
                {"q": {"_id": 2}, "u": {"$set": {"_id": 999}}},  # error: can't modify _id
                {"q": {"_id": 3}, "u": {"$set": {"x": 30}}},
            ],
            "ordered": False,
        },
    )
    # First and third succeed, second errors
    assertSuccessPartial(result, {"ok": 1.0, "n": 2, "nModified": 2})


def test_update_ordered_true_write_errors_has_correct_index(collection):
    """Test writeErrors array contains correct index for the failing statement."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$set": {"x": 10}}},
                {"q": {"_id": 2}, "u": {"$set": {"_id": 999}}},  # error at index 1
            ],
            "ordered": True,
        },
    )
    assertSuccessPartial(result, {"writeErrors": [{"index": 1}]})
