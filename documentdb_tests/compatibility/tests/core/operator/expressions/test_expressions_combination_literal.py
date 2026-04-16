"""
Integration tests for $literal with sibling expression operators.

Covers $literal dollar-sign comparison via $eq.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


# ---------------------------------------------------------------------------
# $literal dollar-sign string comparison via $eq
# ---------------------------------------------------------------------------
def test_literal_dollar_string_eq_match(collection):
    """Test $literal '$1' compared via $eq to field containing '$1' returns true."""
    collection.insert_one({"_id": 1, "price": "$1"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$eq": ["$price", {"$literal": "$1"}]}}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"result": True}], msg="$literal '$1' should match field containing '$1'"
    )


def test_literal_dollar_string_eq_no_match(collection):
    """Test $literal '$1' compared via $eq to field not containing '$1' returns false."""
    collection.insert_one({"_id": 1, "price": "$2.50"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$eq": ["$price", {"$literal": "$1"}]}}}
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"result": False}],
        msg="$literal '$1' should not match field containing '$2.50'",
    )
