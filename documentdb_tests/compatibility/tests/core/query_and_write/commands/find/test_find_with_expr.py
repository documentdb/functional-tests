"""
Tests for $expr in find command contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

BASIC_DOCS = [
    {"_id": 1, "a": 5, "b": 3},
    {"_id": 2, "a": 1, "b": 10},
    {"_id": 3, "a": -1, "b": 0},
]


def test_expr_let_in_find(collection):
    """Test $expr with let variable in find command."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$eq": ["$a", "$$target"]}},
            "let": {"target": 5},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": 5, "b": 3}])


def test_expr_with_collation(collection):
    """Test $expr with collation — string comparison respects collation rules."""
    collection.insert_many([{"_id": 1, "name": "apple"}, {"_id": 2, "name": "Banana"}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$gt": ["$name", "banana"]}},
            "collation": {"locale": "en", "strength": 2},
        },
    )
    assertSuccess(result, [])
