"""
Tests for $expr in aggregate command contexts.

Covers $match, $match with pipeline stages, let variables, and $lookup subpipeline.
"""

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
)
from documentdb_tests.framework.error_codes import (
    LET_UNDEFINED_VARIABLE_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command

BASIC_DOCS = [
    {"_id": 1, "a": 5, "b": 3},
    {"_id": 2, "a": 1, "b": 10},
    {"_id": 3, "a": -1, "b": 0},
]


def test_expr_aggregate_match(collection):
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
            "pipeline": [{"$match": {"$expr": True}}, {"$sort": {"_id": 1}}],
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
    collection.insert_many([{"_id": 1, "price": 80, "tax": 15}, {"_id": 2, "price": 50, "tax": 5}])
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


def test_expr_let_in_aggregate(collection):
    """Test $expr with let variable in aggregate $match."""
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


def test_expr_lookup_basic_eq(database_client):
    """Test $lookup with $expr $eq joining on let variable."""
    orders = database_client.create_collection("orders_test")
    customers = database_client.create_collection("customers_test")
    customers.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}])
    orders.insert_many(
        [
            {"_id": 10, "customer_id": 1, "item": "A"},
            {"_id": 11, "customer_id": 1, "item": "B"},
            {"_id": 12, "customer_id": 2, "item": "C"},
        ]
    )
    result = execute_command(
        customers,
        {
            "aggregate": customers.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": orders.name,
                        "let": {"cust_id": "$_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$customer_id", "$$cust_id"]}}},
                            {"$project": {"_id": 0, "item": 1}},
                        ],
                        "as": "orders",
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "name": "Alice", "orders": [{"item": "A"}, {"item": "B"}]},
            {"_id": 2, "name": "Bob", "orders": [{"item": "C"}]},
        ],
    )


def test_expr_lookup_range_gt(database_client):
    """Test $lookup with $expr $gt for range join."""
    items = database_client.create_collection("items_test")
    thresholds = database_client.create_collection("thresholds_test")
    thresholds.insert_one({"_id": 1, "min_qty": 5})
    items.insert_many([{"_id": 10, "qty": 10}, {"_id": 11, "qty": 3}, {"_id": 12, "qty": 7}])
    result = execute_command(
        thresholds,
        {
            "aggregate": thresholds.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": items.name,
                        "let": {"min": "$min_qty"},
                        "pipeline": [
                            {"$match": {"$expr": {"$gt": ["$qty", "$$min"]}}},
                            {"$project": {"_id": 0, "qty": 1}},
                            {"$sort": {"qty": 1}},
                        ],
                        "as": "above_min",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "min_qty": 5, "above_min": [{"qty": 7}, {"qty": 10}]}])


def test_expr_lookup_arithmetic(database_client):
    """Test $lookup with $expr using arithmetic on let variable."""
    orders = database_client.create_collection("orders_arith")
    limits = database_client.create_collection("limits_arith")
    limits.insert_one({"_id": 1, "base_limit": 50})
    orders.insert_many([{"_id": 10, "amount": 120}, {"_id": 11, "amount": 80}])
    result = execute_command(
        limits,
        {
            "aggregate": limits.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": orders.name,
                        "let": {"limit": "$base_limit"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {"$gt": ["$amount", {"$multiply": ["$$limit", 2]}]}
                                }
                            },
                            {"$project": {"_id": 0, "amount": 1}},
                        ],
                        "as": "over_double",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "base_limit": 50, "over_double": [{"amount": 120}]}])


def test_expr_lookup_let_null(database_client):
    """Test $lookup with let variable resolving to null."""
    inner = database_client.create_collection("inner_null")
    outer = database_client.create_collection("outer_null")
    outer.insert_one({"_id": 1, "val": None})
    inner.insert_many([{"_id": 10, "x": None}, {"_id": 11, "x": 1}])
    result = execute_command(
        outer,
        {
            "aggregate": outer.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": inner.name,
                        "let": {"v": "$val"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$x", "$$v"]}}},
                            {"$project": {"_id": 1}},
                        ],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "val": None, "matched": [{"_id": 10}]}])


def test_expr_lookup_let_missing_field(database_client):
    """Test $lookup with let variable from missing field — resolves to missing, not null."""
    inner = database_client.create_collection("inner_miss")
    outer = database_client.create_collection("outer_miss")
    outer.insert_one({"_id": 1})
    inner.insert_many([{"_id": 10, "x": None}, {"_id": 11, "x": 1}])
    result = execute_command(
        outer,
        {
            "aggregate": outer.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": inner.name,
                        "let": {"v": "$val"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$x", "$$v"]}}},
                            {"$project": {"_id": 1}},
                        ],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Missing field in let resolves to missing, which doesn't match null
    assertSuccess(result, [{"_id": 1, "matched": []}])


def test_expr_lookup_no_match(database_client):
    """Test $lookup with $expr where no inner docs match — as field is empty array."""
    inner = database_client.create_collection("inner_nomatch")
    outer = database_client.create_collection("outer_nomatch")
    outer.insert_one({"_id": 1, "val": 999})
    inner.insert_many([{"_id": 10, "x": 1}, {"_id": 11, "x": 2}])
    result = execute_command(
        outer,
        {
            "aggregate": outer.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": inner.name,
                        "let": {"v": "$val"},
                        "pipeline": [{"$match": {"$expr": {"$eq": ["$x", "$$v"]}}}],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "val": 999, "matched": []}])


def test_expr_lookup_undefined_variable(database_client):
    """Test $lookup with $expr referencing undefined let variable — error."""
    inner = database_client.create_collection("inner_undef")
    outer = database_client.create_collection("outer_undef")
    outer.insert_one({"_id": 1})
    inner.insert_one({"_id": 10})
    result = execute_command(
        outer,
        {
            "aggregate": outer.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": inner.name,
                        "let": {},
                        "pipeline": [{"$match": {"$expr": {"$eq": ["$x", "$$undefined_var"]}}}],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, LET_UNDEFINED_VARIABLE_ERROR)
