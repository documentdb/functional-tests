"""
Tests for $expr in $match stage.

Covers $expr basic matching, combined with regular query operators,
$and with multiple $expr, truthiness, error handling, implicit array
behavior, and $match with $expr after other pipeline stages.
"""

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
)
from documentdb_tests.framework.error_codes import (
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command

BASIC_DOCS = [
    {"_id": 1, "a": 5, "b": 3},
    {"_id": 2, "a": 1, "b": 10},
    {"_id": 3, "a": -1, "b": 0},
]


def test_expr_match(collection):
    """Test $expr in aggregate $match — same results as find."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$expr": {"$gt": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": 5, "b": 3}])


def test_expr_match_combined_with_regular_query(collection):
    """Test $expr combined with regular query operator in $match."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$expr": {"$gt": ["$a", 0]}, "b": {"$lt": 10}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": 5, "b": 3}])


def test_expr_match_with_and(collection):
    """Test $match with $and containing two $expr clauses."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$match": {
                        "$and": [
                            {"$expr": {"$gt": ["$a", 0]}},
                            {"$expr": {"$lt": ["$b", 10]}},
                        ]
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": 5, "b": 3}])


def test_expr_match_truthiness(collection):
    """Test $expr truthiness in $match — literal true matches all."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$expr": True}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, BASIC_DOCS)


def test_expr_match_error(collection):
    """Test $expr with invalid operator in $match — returns error."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$expr": {"$invalidOp": 1}}}],
            "cursor": {},
        },
    )
    assertFailureCode(result, UNRECOGNIZED_EXPRESSION_ERROR)


def test_expr_match_array_no_implicit(collection):
    """Test $expr in $match does NOT do implicit array element matching."""
    collection.insert_one({"_id": 1, "a": [1, 5, 10, 15]})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$expr": {"$gt": ["$a", 12]}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": [1, 5, 10, 15]}])


def test_expr_match_after_group(collection):
    """Test $expr in $match after $group — references grouped fields."""
    collection.insert_many(
        [
            {"_id": 1, "cat": "A", "val": 10},
            {"_id": 2, "cat": "A", "val": 20},
            {"_id": 3, "cat": "B", "val": 5},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
                {"$match": {"$expr": {"$gt": ["$total", 10]}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": "A", "total": 30}])


def test_expr_match_after_addfields(collection):
    """Test $expr in $match after $addFields references computed field."""
    collection.insert_many(
        [
            {"_id": 1, "price": 80, "tax": 15},
            {"_id": 2, "price": 50, "tax": 5},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"total": {"$add": ["$price", "$tax"]}}},
                {"$match": {"$expr": {"$gt": ["$total", 90]}}},
                {"$project": {"_id": 1, "total": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "total": 95}])


def test_expr_match_after_unwind(collection):
    """Test $expr in $match after $unwind references unwound field."""
    collection.insert_one({"_id": 1, "items": [{"v": 10}, {"v": 3}]})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$unwind": "$items"},
                {"$match": {"$expr": {"$gt": ["$items.v", 5]}}},
                {"$project": {"_id": 1, "v": "$items.v"}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "v": 10}])


def test_expr_match_with_aggregate_let(collection):
    """Test $expr in $match using aggregate command-level let variable."""
    collection.insert_many(BASIC_DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$expr": {"$eq": ["$a", "$$target"]}}}],
            "cursor": {},
            "let": {"target": 5},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": 5, "b": 3}])
