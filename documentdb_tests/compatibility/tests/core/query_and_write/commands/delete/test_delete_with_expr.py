"""
Tests for $expr in delete command contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

BASIC_DOCS = [
    {"_id": 1, "a": 5, "b": 3},
    {"_id": 2, "a": 1, "b": 10},
    {"_id": 3, "a": -1, "b": 0},
]


def test_expr_in_delete_many(collection):
    """Test $expr in deleteMany filter."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"$expr": {"$lt": ["$a", 0]}}, "limit": 0}],
        },
    )
    assertSuccess(result, {"n": 1, "ok": 1.0}, raw_res=True)


def test_expr_let_in_delete(collection):
    """Test $expr with let variable in delete command."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"$expr": {"$eq": ["$a", "$$target"]}}, "limit": 0}],
            "let": {"target": -1},
        },
    )
    assertSuccess(result, {"n": 1, "ok": 1.0}, raw_res=True)


def test_expr_delete_with_in(collection):
    """Test $expr in deleteMany with $in on array field."""
    collection.insert_many([{"_id": 1, "tags": [True, False]}, {"_id": 2, "tags": [False]}])
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"$expr": {"$in": [True, "$tags"]}}, "limit": 0}],
        },
    )
    assertSuccess(result, {"n": 1, "ok": 1.0}, raw_res=True)


def test_expr_delete_with_cond(collection):
    """Test $expr in deleteMany with $cond expression."""
    collection.insert_many(
        [
            {"_id": 1, "price": 100, "discount": 0.2},
            {"_id": 2, "price": 50, "discount": 0.1},
        ]
    )
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [
                {
                    "q": {
                        "$expr": {
                            "$lt": [
                                {
                                    "$cond": [
                                        {"$gt": ["$discount", 0]},
                                        {"$multiply": ["$price", {"$subtract": [1, "$discount"]}]},
                                        "$price",
                                    ]
                                },
                                60,
                            ]
                        }
                    },
                    "limit": 0,
                }
            ],
        },
    )
    assertSuccess(result, {"n": 1, "ok": 1.0}, raw_res=True)
