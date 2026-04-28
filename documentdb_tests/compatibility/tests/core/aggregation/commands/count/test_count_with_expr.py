"""
Tests for $expr in count command contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

BASIC_DOCS = [
    {"_id": 1, "a": 5, "b": 3},
    {"_id": 2, "a": 1, "b": 10},
    {"_id": 3, "a": -1, "b": 0},
]


def test_expr_in_count(collection):
    """Test $expr in count command."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "count": collection.name,
            "query": {"$expr": {"$gt": ["$a", 0]}},
        },
    )
    assertSuccess(result, 2, raw_res=True, transform=lambda r: r.get("n"))
