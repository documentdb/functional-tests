"""Representative query operator wiring tests for the count command.

One test per operator category confirms the count command's query parameter
is correctly wired to the query engine. Exhaustive operator behavior is
tested in core/operator/query/.
"""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Query Operator Wiring]: the count command's query parameter supports
# comparison, logical, array, bitwise, miscellaneous, and expression operators.
COUNT_QUERY_OPERATOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_empty_doc",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        command=lambda ctx: {"count": ctx.collection, "query": {}},
        expected={"n": 3, "ok": 1.0},
        msg="count with empty query should match all documents",
    ),
    # Comparison operators.
    CommandTestCase(
        "query_eq",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 1}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$eq": 1}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $eq in query",
    ),
    CommandTestCase(
        "query_ne",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$ne": 2}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $ne in query",
    ),
    CommandTestCase(
        "query_gt",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$gt": 4}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $gt in query",
    ),
    CommandTestCase(
        "query_gte",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$gte": 5}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $gte in query",
    ),
    CommandTestCase(
        "query_lt",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$lt": 5}}},
        expected={"n": 1, "ok": 1.0},
        msg="count should support $lt in query",
    ),
    CommandTestCase(
        "query_lte",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$lte": 5}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $lte in query",
    ),
    CommandTestCase(
        "query_in",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$in": [1, 10]}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $in in query",
    ),
    CommandTestCase(
        "query_nin",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$nin": [1, 10]}}},
        expected={"n": 1, "ok": 1.0},
        msg="count should support $nin in query",
    ),
    # Logical operators.
    CommandTestCase(
        "query_and",
        docs=[
            {"_id": 1, "x": 1, "y": 10},
            {"_id": 2, "x": 5, "y": 10},
            {"_id": 3, "x": 5, "y": 20},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"$and": [{"x": {"$gt": 2}}, {"y": 10}]},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should support $and in query",
    ),
    CommandTestCase(
        "query_or",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"$or": [{"x": 1}, {"x": 10}]},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should support $or in query",
    ),
    CommandTestCase(
        "query_nor",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 5}, {"_id": 3, "x": 10}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"$nor": [{"x": 1}, {"x": 10}]},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should support $nor in query",
    ),
    CommandTestCase(
        "query_not",
        docs=[{"_id": 1, "x": 3}, {"_id": 2, "x": 7}, {"_id": 3, "x": 10}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"x": {"$not": {"$gt": 5}}},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should support $not in query",
    ),
    # Array operators.
    CommandTestCase(
        "query_all",
        docs=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [1, 3]},
            {"_id": 3, "arr": [2, 3]},
        ],
        command=lambda ctx: {"count": ctx.collection, "query": {"arr": {"$all": [1, 3]}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $all in query",
    ),
    CommandTestCase(
        "query_elemMatch",
        docs=[
            {"_id": 1, "arr": [{"a": 1, "b": 2}]},
            {"_id": 2, "arr": [{"a": 1, "b": 5}]},
            {"_id": 3, "arr": [{"a": 3, "b": 2}]},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"arr": {"$elemMatch": {"a": 1, "b": {"$gt": 1}}}},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should support $elemMatch in query",
    ),
    CommandTestCase(
        "query_size",
        docs=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [1]},
            {"_id": 3, "arr": [1, 2]},
        ],
        command=lambda ctx: {"count": ctx.collection, "query": {"arr": {"$size": 2}}},
        expected={"n": 1, "ok": 1.0},
        msg="count should support $size in query",
    ),
    # Bitwise operators.
    CommandTestCase(
        "query_bitsAllSet",
        docs=[{"_id": 1, "flags": 7}, {"_id": 2, "flags": 3}, {"_id": 3, "flags": 15}],
        command=lambda ctx: {"count": ctx.collection, "query": {"flags": {"$bitsAllSet": 5}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $bitsAllSet in query",
    ),
    CommandTestCase(
        "query_bitsAllClear",
        docs=[{"_id": 1, "flags": 7}, {"_id": 2, "flags": 8}, {"_id": 3, "flags": 15}],
        command=lambda ctx: {"count": ctx.collection, "query": {"flags": {"$bitsAllClear": 7}}},
        expected={"n": 1, "ok": 1.0},
        msg="count should support $bitsAllClear in query",
    ),
    CommandTestCase(
        "query_bitsAnySet",
        docs=[{"_id": 1, "flags": 4}, {"_id": 2, "flags": 8}, {"_id": 3, "flags": 16}],
        command=lambda ctx: {"count": ctx.collection, "query": {"flags": {"$bitsAnySet": 6}}},
        expected={"n": 1, "ok": 1.0},
        msg="count should support $bitsAnySet in query",
    ),
    CommandTestCase(
        "query_bitsAnyClear",
        docs=[{"_id": 1, "flags": 7}, {"_id": 2, "flags": 3}, {"_id": 3, "flags": 15}],
        command=lambda ctx: {"count": ctx.collection, "query": {"flags": {"$bitsAnyClear": 12}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $bitsAnyClear in query",
    ),
    # Miscellaneous operators.
    CommandTestCase(
        "query_exists",
        docs=[{"_id": 1, "x": 1}, {"_id": 2}, {"_id": 3, "x": 10}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$exists": True}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $exists in query",
    ),
    CommandTestCase(
        "query_type",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": "hello"}, {"_id": 3, "x": 3.14}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$type": "string"}}},
        expected={"n": 1, "ok": 1.0},
        msg="count should support $type in query",
    ),
    CommandTestCase(
        "query_regex",
        docs=[{"_id": 1, "s": "hello"}, {"_id": 2, "s": "world"}, {"_id": 3, "s": "help"}],
        command=lambda ctx: {"count": ctx.collection, "query": {"s": {"$regex": "^hel"}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $regex in query",
    ),
    CommandTestCase(
        "query_mod",
        docs=[{"_id": 1, "x": 3}, {"_id": 2, "x": 6}, {"_id": 3, "x": 7}],
        command=lambda ctx: {"count": ctx.collection, "query": {"x": {"$mod": [3, 0]}}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $mod in query",
    ),
    CommandTestCase(
        "query_expr",
        docs=[{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 1, "b": 10}, {"_id": 3, "a": 4, "b": 4}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"$expr": {"$gt": ["$a", "$b"]}},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should support $expr in query",
    ),
    CommandTestCase(
        "query_where",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}, {"_id": 3, "x": 3}],
        command=lambda ctx: {"count": ctx.collection, "query": {"$where": "this.x > 1"}},
        expected={"n": 2, "ok": 1.0},
        msg="count should support $where in query",
    ),
    CommandTestCase(
        "query_jsonSchema",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": "hello"}, {"_id": 3, "x": 3}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {
                "$jsonSchema": {
                    "properties": {"x": {"bsonType": "int"}},
                    "required": ["x"],
                }
            },
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should support $jsonSchema in query",
    ),
    # Geospatial operators.
    CommandTestCase(
        "query_geoWithin",
        docs=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [50, 50]},
            {"_id": 3, "loc": [1, 1]},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"loc": {"$geoWithin": {"$center": [[0, 0], 10]}}},
        },
        expected={"n": 2, "ok": 1.0},
        msg="count should support $geoWithin in query",
    ),
    CommandTestCase(
        "query_geoIntersects",
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {
                "loc": {
                    "$geoIntersects": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                        }
                    }
                }
            },
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should support $geoIntersects in query",
    ),
    CommandTestCase(
        "query_near",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {
                "loc": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [0, 0]},
                        "$maxDistance": 100,
                    }
                }
            },
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should support $near in query",
    ),
    CommandTestCase(
        "query_nearSphere",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {
                "loc": {
                    "$nearSphere": {
                        "$geometry": {"type": "Point", "coordinates": [0, 0]},
                        "$maxDistance": 100,
                    }
                }
            },
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should support $nearSphere in query",
    ),
    # Text search.
    CommandTestCase(
        "query_text",
        indexes=[IndexModel([("s", "text")])],
        docs=[{"_id": 1, "s": "hello world"}, {"_id": 2, "s": "goodbye"}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {"$text": {"$search": "hello"}},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should support $text in query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COUNT_QUERY_OPERATOR_TESTS))
def test_count_query_operators(database_client, collection, test):
    """Test count command query operator wiring."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
