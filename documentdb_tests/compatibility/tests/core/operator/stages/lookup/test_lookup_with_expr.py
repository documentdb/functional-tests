"""
Tests for $expr in $lookup subpipeline.

Covers $lookup with $expr join conditions, let variables,
arithmetic in $expr, null/missing field handling, and error cases.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import LET_UNDEFINED_VARIABLE_ERROR
from documentdb_tests.framework.executor import execute_command


@pytest.mark.aggregate
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
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [
                                            "$customer_id",
                                            "$$cust_id",
                                        ]
                                    }
                                }
                            },
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
            {
                "_id": 1,
                "name": "Alice",
                "orders": [{"item": "A"}, {"item": "B"}],
            },
            {"_id": 2, "name": "Bob", "orders": [{"item": "C"}]},
        ],
        msg="$lookup with $expr $eq should join on let variable",
    )


@pytest.mark.aggregate
def test_expr_lookup_range_gt(database_client):
    """Test $lookup with $expr $gt for range join."""
    items = database_client.create_collection("items_test")
    thresholds = database_client.create_collection("thresholds_test")
    thresholds.insert_one({"_id": 1, "min_qty": 5})
    items.insert_many(
        [
            {"_id": 10, "qty": 10},
            {"_id": 11, "qty": 3},
            {"_id": 12, "qty": 7},
        ]
    )
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
    assertSuccess(
        result,
        [
            {
                "_id": 1,
                "min_qty": 5,
                "above_min": [{"qty": 7}, {"qty": 10}],
            }
        ],
        msg="$lookup with $expr $gt should filter by range condition",
    )


@pytest.mark.aggregate
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
                                    "$expr": {
                                        "$gt": [
                                            "$amount",
                                            {"$multiply": ["$$limit", 2]},
                                        ]
                                    }
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
    assertSuccess(
        result,
        [{"_id": 1, "base_limit": 50, "over_double": [{"amount": 120}]}],
        msg="$lookup with $expr should support arithmetic on let variables",
    )


@pytest.mark.aggregate
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
    assertSuccess(
        result,
        [{"_id": 1, "val": None, "matched": [{"_id": 10}]}],
        msg="$lookup with let variable resolving to null should match null values",
    )


@pytest.mark.aggregate
def test_expr_lookup_let_missing_field(database_client):
    """Test $lookup with let variable from missing field."""
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
    assertSuccess(
        result,
        [{"_id": 1, "matched": []}],
        msg="$lookup with let variable from missing field should not match any docs",
    )


@pytest.mark.aggregate
def test_expr_lookup_no_match(database_client):
    """Test $lookup with $expr where no inner docs match."""
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
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$x", "$$v"]}}},
                        ],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "val": 999, "matched": []}],
        msg="$lookup with $expr should return empty array when no docs match",
    )


@pytest.mark.aggregate
def test_expr_lookup_undefined_variable(database_client):
    """Test $lookup with $expr referencing undefined let variable."""
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
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$x", "$$undefined_var"]}}},
                        ],
                        "as": "matched",
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        LET_UNDEFINED_VARIABLE_ERROR,
        msg="$lookup with $expr referencing undefined let variable should fail",
    )
