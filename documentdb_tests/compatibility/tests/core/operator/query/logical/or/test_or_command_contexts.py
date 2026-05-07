"""
Tests for $or in various command contexts.

Tests $or with $expr, and in find, update, delete, findAndModify,
count, and distinct command filters.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

DOCS = [
    {"_id": 1, "a": 5, "b": 3, "c": 1},
    {"_id": 2, "a": 1, "b": 3, "c": 2},
    {"_id": 3, "a": 5, "b": 3, "c": 3},
]


def test_or_with_expr(collection):
    """Test $or containing $expr clause."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$or": [{"$expr": {"$gt": ["$a", "$b"]}}, {"c": 2}]},
        },
    )
    assertSuccess(
        result,
        [DOCS[0], DOCS[1], DOCS[2]],
        msg="$or with $expr matches docs where a > b or c=2",
        ignore_doc_order=True,
    )


def test_or_inside_expr(collection):
    """Test $or inside $expr."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$expr": {"$or": [{"$gt": ["$a", 4]}, {"$eq": ["$c", 2]}]}},
        },
    )
    assertSuccess(
        result,
        [DOCS[0], DOCS[1], DOCS[2]],
        msg="$or inside $expr matches docs where a > 4 or c == 2",
        ignore_doc_order=True,
    )


def test_or_in_update_filter(collection):
    """Test $or in update command filter."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"$or": [{"a": 5}, {"c": 2}]}, "u": {"$set": {"x": 1}}, "multi": True}
            ],
        },
    )
    assertSuccess(
        result,
        {"n": 3, "nModified": 3, "ok": 1.0},
        raw_res=True,
        msg="$or in update filter updates correct docs",
    )


def test_or_in_delete_filter(collection):
    """Test $or in delete command filter."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"$or": [{"c": 1}, {"c": 3}]}, "limit": 0}],
        },
    )
    assertSuccess(
        result, {"n": 2, "ok": 1.0}, raw_res=True, msg="$or in delete filter deletes correct docs"
    )


def test_or_in_count(collection):
    """Test $or in count command filter."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {"count": collection.name, "query": {"$or": [{"a": 5}, {"c": 2}]}},
    )
    assertSuccess(
        result, {"n": 3, "ok": 1.0}, raw_res=True, msg="$or in count returns correct count"
    )


def test_or_in_distinct(collection):
    """Test $or in distinct command filter."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "distinct": collection.name,
            "key": "c",
            "query": {"$or": [{"a": 5}]},
        },
    )
    assertSuccess(
        result,
        {"values": [1, 3], "ok": 1.0},
        raw_res=True,
        msg="$or in distinct returns correct values",
    )
