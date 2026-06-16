"""
Tests for $expr in update command contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

BASIC_DOCS = [
    {"_id": 1, "a": 5, "b": 3},
    {"_id": 2, "a": 1, "b": 10},
    {"_id": 3, "a": -1, "b": 0},
]


def test_expr_in_update_many(collection):
    """Test $expr in updateMany filter."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"$expr": {"$gt": ["$a", "$b"]}},
                    "u": {"$set": {"flag": True}},
                    "multi": True,
                }
            ],
        },
    )
    assertSuccess(result, {"n": 1, "nModified": 1, "ok": 1.0}, raw_res=True)


def test_expr_let_in_update(collection):
    """Test $expr with let variable in update command."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"$expr": {"$eq": ["$a", "$$target"]}},
                    "u": {"$set": {"found": True}},
                    "multi": True,
                }
            ],
            "let": {"target": 1},
        },
    )
    assertSuccess(result, {"n": 1, "nModified": 1, "ok": 1.0}, raw_res=True)


def test_expr_now_in_update_with_let(collection):
    """Test $expr with let variable in filter, $$NOW in pipeline update."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"$expr": {"$eq": ["$a", "$$target"]}},
                    "u": [{"$set": {"updated_at": "$$NOW"}}],
                    "multi": True,
                }
            ],
            "let": {"target": 5},
        },
    )
    assertSuccess(result, {"n": 1, "nModified": 1, "ok": 1.0}, raw_res=True)
