"""
Tests for $expr in distinct command contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_expr_in_distinct(collection):
    """Test $expr in distinct command."""
    collection.insert_many(
        [
            {"_id": 1, "cat": "A", "val": 10},
            {"_id": 2, "cat": "B", "val": 5},
            {"_id": 3, "cat": "A", "val": 3},
        ]
    )
    result = execute_command(
        collection,
        {
            "distinct": collection.name,
            "key": "cat",
            "query": {"$expr": {"$gt": ["$val", 4]}},
        },
    )
    assertSuccess(
        result, sorted(["A", "B"]), raw_res=True, transform=lambda r: sorted(r.get("values", []))
    )
