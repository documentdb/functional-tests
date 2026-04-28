"""
Tests for $expr in findAndModify command contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

BASIC_DOCS = [
    {"_id": 1, "a": 5, "b": 3},
    {"_id": 2, "a": 1, "b": 10},
    {"_id": 3, "a": -1, "b": 0},
]


def test_expr_in_find_and_modify(collection):
    """Test $expr in findAndModify query."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"$expr": {"$gt": ["$a", "$b"]}},
            "update": {"$set": {"modified": True}},
            "sort": {"_id": 1},
        },
    )
    assertSuccess(
        result, {"_id": 1, "a": 5, "b": 3}, raw_res=True, transform=lambda r: r.get("value")
    )


def test_expr_findandmodify_literal_true(collection):
    """Test $expr with literal true in findAndModify — matches all, returns first by sort."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"$expr": True},
            "update": {"$set": {"touched": True}},
            "sort": {"_id": 1},
        },
    )
    assertSuccess(
        result, {"_id": 1, "a": 5, "b": 3}, raw_res=True, transform=lambda r: r.get("value")
    )
