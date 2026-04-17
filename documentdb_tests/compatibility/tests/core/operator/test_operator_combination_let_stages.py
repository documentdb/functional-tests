"""
Integration tests for $let with pipeline stages.

Covers $let in $addFields, $let in $match with $expr, $let in $group,
$let in $redact, and $let in $lookup sub-pipeline.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


# ---------------------------------------------------------------------------
# $let in $addFields
# ---------------------------------------------------------------------------
def test_let_in_addfields(collection):
    """Test $let used inside $addFields stage."""
    collection.insert_one({"_id": 1, "price": 100, "tax_rate": 0.08})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$addFields": {
                        "total": {
                            "$let": {
                                "vars": {"tax": {"$multiply": ["$price", "$tax_rate"]}},
                                "in": {"$add": ["$price", "$$tax"]},
                            }
                        }
                    }
                },
                {"$project": {"_id": 0, "total": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"total": 108.0}], msg="$let in $addFields should compute total")


# ---------------------------------------------------------------------------
# $let in $match with $expr
# ---------------------------------------------------------------------------
def test_let_in_match_expr(collection):
    """Test $let used inside $match with $expr."""
    collection.insert_many(
        [
            {"_id": 1, "price": 100, "discount": 10},
            {"_id": 2, "price": 50, "discount": 5},
            {"_id": 3, "price": 200, "discount": 50},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$let": {
                                "vars": {
                                    "net": {"$subtract": ["$price", "$discount"]},
                                },
                                "in": {"$gt": ["$$net", 80]},
                            }
                        }
                    }
                },
                {"$project": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"_id": 1}, {"_id": 3}], msg="$let in $match $expr should filter by net > 80"
    )


# ---------------------------------------------------------------------------
# $let in $group
# ---------------------------------------------------------------------------
def test_let_in_group_id(collection):
    """Test $let used as $group _id expression."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "price": 100, "discount": 10},
            {"_id": 2, "category": "A", "price": 200, "discount": 20},
            {"_id": 3, "category": "B", "price": 150, "discount": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": {
                            "$let": {
                                "vars": {"net": {"$subtract": ["$price", "$discount"]}},
                                "in": {"$cond": [{"$gte": ["$$net", 150]}, "high", "low"]},
                            }
                        },
                        "count": {"$sum": 1},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "high", "count": 1}, {"_id": "low", "count": 2}],
        msg="$let in $group _id should classify documents",
        ignore_doc_order=True,
    )


def test_let_in_group_accumulator(collection):
    """Test $let used inside $group accumulator expression."""
    collection.insert_many(
        [
            {"_id": 1, "price": 100, "discount": 10},
            {"_id": 2, "price": 200, "discount": 20},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "total_net": {
                            "$sum": {
                                "$let": {
                                    "vars": {"net": {"$subtract": ["$price", "$discount"]}},
                                    "in": "$$net",
                                }
                            }
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "total_net": 270}],
        msg="$let in $group accumulator should sum net prices",
    )


# ---------------------------------------------------------------------------
# $let in $redact
# ---------------------------------------------------------------------------
def test_let_in_redact_descend_prune(collection):
    """Test $let in $redact with $cond choosing $$DESCEND or $$PRUNE."""
    collection.insert_one(
        {
            "_id": 1,
            "level": 1,
            "public": True,
            "nested": {"level": 2, "public": False, "data": "secret"},
        }
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$redact": {
                        "$let": {
                            "vars": {"is_public": "$public"},
                            "in": {
                                "$cond": [
                                    {"$eq": ["$$is_public", True]},
                                    "$$DESCEND",
                                    "$$PRUNE",
                                ]
                            },
                        }
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "level": 1, "public": True}],
        msg="$let in $redact should prune non-public subdocuments",
    )


def test_let_in_redact_keep(collection):
    """Test $let in $redact with $$KEEP to retain entire document."""
    collection.insert_one({"_id": 1, "access": "admin", "data": {"secret": 42}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$redact": {
                        "$let": {
                            "vars": {"role": "$access"},
                            "in": {"$cond": [{"$eq": ["$$role", "admin"]}, "$$KEEP", "$$PRUNE"]},
                        }
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "access": "admin", "data": {"secret": 42}}],
        msg="$let in $redact with $$KEEP should retain entire document",
    )


# ---------------------------------------------------------------------------
# $let in $lookup sub-pipeline
# ---------------------------------------------------------------------------
def test_let_in_lookup_subpipeline(database_client):
    """Test $let used inside $lookup sub-pipeline."""
    orders = database_client["orders"]
    products = database_client["products"]
    orders.insert_many([{"_id": 1, "product_id": 100}, {"_id": 2, "product_id": 200}])
    products.insert_many([{"_id": 100, "price": 10}, {"_id": 200, "price": 25}])
    result = execute_command(
        orders,
        {
            "aggregate": orders.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$lookup": {
                        "from": products.name,
                        "localField": "product_id",
                        "foreignField": "_id",
                        "pipeline": [
                            {
                                "$project": {
                                    "_id": 0,
                                    "doubled": {
                                        "$let": {
                                            "vars": {"p": "$price"},
                                            "in": {"$multiply": ["$$p", 2]},
                                        }
                                    },
                                }
                            }
                        ],
                        "as": "info",
                    }
                },
                {"$project": {"_id": 1, "info": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "info": [{"doubled": 20}]},
            {"_id": 2, "info": [{"doubled": 50}]},
        ],
        msg="$let inside $lookup sub-pipeline should compute doubled price",
    )


def test_let_vars_shadow_lookup_let(database_client):
    """Test $let vars shadow $lookup let variable of the same name."""
    orders = database_client["orders"]
    products = database_client["products"]
    orders.insert_one({"_id": 1, "qty": 5})
    products.insert_one({"_id": 100, "price": 10})
    result = execute_command(
        orders,
        {
            "aggregate": orders.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": products.name,
                        "let": {"x": "$qty"},
                        "pipeline": [
                            {
                                "$project": {
                                    "_id": 0,
                                    "result": {
                                        "$let": {
                                            "vars": {"x": 999},
                                            "in": "$$x",
                                        }
                                    },
                                }
                            }
                        ],
                        "as": "info",
                    }
                },
                {"$project": {"_id": 0, "info": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"info": [{"result": 999}]}],
        msg="$let vars should shadow $lookup let variable of same name",
    )


def test_lookup_let_var_accessible_inside_let_in(database_client):
    """Test $lookup let variable is accessible inside $let 'in' expression."""
    orders = database_client["orders"]
    products = database_client["products"]
    orders.insert_one({"_id": 1, "qty": 3})
    products.insert_one({"_id": 100, "price": 10})
    result = execute_command(
        orders,
        {
            "aggregate": orders.name,
            "pipeline": [
                {
                    "$lookup": {
                        "from": products.name,
                        "let": {"order_qty": "$qty"},
                        "pipeline": [
                            {
                                "$project": {
                                    "_id": 0,
                                    "total": {
                                        "$let": {
                                            "vars": {"p": "$price"},
                                            "in": {"$multiply": ["$$p", "$$order_qty"]},
                                        }
                                    },
                                }
                            }
                        ],
                        "as": "info",
                    }
                },
                {"$project": {"_id": 0, "info": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"info": [{"total": 30}]}],
        msg="$lookup let var should be accessible inside $let in expression",
    )
