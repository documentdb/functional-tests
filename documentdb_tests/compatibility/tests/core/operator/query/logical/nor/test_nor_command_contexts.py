"""
Tests for $nor query operator in find command contexts.

Covers $nor in find with projection, sort, and limit/skip.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

DOCS = [
    {"_id": 1, "val": 5, "status": "a"},
    {"_id": 2, "val": 15, "status": "b"},
    {"_id": 3, "val": 25, "status": "a"},
]


def test_nor_in_find(collection):
    """Test $nor in find command filter."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$nor": [{"val": {"$gt": 10}}]}}
    )
    assertSuccess(
        result, [{"_id": 1, "val": 5, "status": "a"}], msg="$nor should work in find filter"
    )


def test_nor_with_projection(collection):
    """Test $nor in query with projection."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$nor": [{"val": {"$gt": 10}}]},
            "projection": {"val": 1},
        },
    )
    assertSuccess(result, [{"_id": 1, "val": 5}], msg="$nor should work with projection")


def test_nor_with_sort(collection):
    """Test $nor in query with sort."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$nor": [{"status": "b"}]},
            "sort": {"val": -1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 3, "val": 25, "status": "a"}, {"_id": 1, "val": 5, "status": "a"}],
        msg="$nor should work with sort",
    )


def test_nor_with_limit_skip(collection):
    """Test $nor in query with limit and skip."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$nor": [{"status": "b"}]},
            "sort": {"val": 1},
            "limit": 1,
            "skip": 1,
        },
    )
    assertSuccess(
        result,
        [{"_id": 3, "val": 25, "status": "a"}],
        msg="$nor should work with limit and skip",
    )
