"""
Update command context tests for $mul update field operator.

Tests $mul in updateMany and upsert contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_mul_update_many(collection):
    """Test $mul in updateMany multiplies all matched document values."""
    collection.insert_many(
        [
            {"_id": 1, "val": 10, "group": "a"},
            {"_id": 2, "val": 20, "group": "a"},
            {"_id": 3, "val": 30, "group": "b"},
        ]
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"group": "a"}, "u": {"$mul": {"val": 2}}, "multi": True}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"group": "a"}, "sort": {"_id": 1}},
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "val": 20, "group": "a"},
            {"_id": 2, "val": 40, "group": "a"},
        ],
        msg="$mul in updateMany should multiply all matched document values",
    )


def test_mul_upsert_missing_doc(collection):
    """Test $mul with upsert on non-existent doc creates field with zero."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$mul": {"val": 5}}, "upsert": True}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "val": 0}],
        msg="$mul with upsert on non-existent doc should create with val=0",
    )
