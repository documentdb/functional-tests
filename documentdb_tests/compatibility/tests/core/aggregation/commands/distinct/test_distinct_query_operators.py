"""Representative query operator wiring tests for the distinct command.

One test per operator category confirms the distinct command's query parameter
is correctly wired to the query engine. Exhaustive operator behavior is
tested in core/operator/query/.
"""

from __future__ import annotations

from typing import Any

import pytest
from bson import Int64
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Query Operator Wiring]: the distinct command's query parameter supports
# comparison, logical, array, element, evaluation, and bitwise operators.
DISTINCT_QUERY_OPERATOR_TESTS: list[CommandTestCase] = [
    # Comparison operators.
    CommandTestCase(
        "query_eq",
        docs=[{"_id": 1, "x": "a", "n": 1}, {"_id": 2, "x": "b", "n": 2}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$eq": 1}},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should support $eq in query",
    ),
    CommandTestCase(
        "query_ne",
        docs=[{"_id": 1, "x": "a", "n": 1}, {"_id": 2, "x": "b", "n": 2}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$ne": 1}},
        },
        expected={"values": ["b"], "ok": 1.0},
        msg="distinct should support $ne in query",
    ),
    CommandTestCase(
        "query_gt",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 5},
            {"_id": 3, "x": "c", "n": 10},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$gt": 4}},
        },
        expected={"values": ["b", "c"], "ok": 1.0},
        msg="distinct should support $gt in query",
    ),
    CommandTestCase(
        "query_gte",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 5},
            {"_id": 3, "x": "c", "n": 10},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$gte": 5}},
        },
        expected={"values": ["b", "c"], "ok": 1.0},
        msg="distinct should support $gte in query",
    ),
    CommandTestCase(
        "query_lt",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 5},
            {"_id": 3, "x": "c", "n": 10},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$lt": 5}},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should support $lt in query",
    ),
    CommandTestCase(
        "query_lte",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 5},
            {"_id": 3, "x": "c", "n": 10},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$lte": 5}},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should support $lte in query",
    ),
    CommandTestCase(
        "query_in",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 2},
            {"_id": 3, "x": "c", "n": 3},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$in": [1, 3]}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $in in query",
    ),
    CommandTestCase(
        "query_nin",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 2},
            {"_id": 3, "x": "c", "n": 3},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$nin": [1, 3]}},
        },
        expected={"values": ["b"], "ok": 1.0},
        msg="distinct should support $nin in query",
    ),
    # Logical operators.
    CommandTestCase(
        "query_and",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 5},
            {"_id": 3, "x": "c", "n": 10},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"$and": [{"n": {"$gt": 1}}, {"n": {"$lt": 10}}]},
        },
        expected={"values": ["b"], "ok": 1.0},
        msg="distinct should support $and in query",
    ),
    CommandTestCase(
        "query_or",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 5},
            {"_id": 3, "x": "c", "n": 10},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"$or": [{"n": 1}, {"n": 10}]},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $or in query",
    ),
    CommandTestCase(
        "query_nor",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 5},
            {"_id": 3, "x": "c", "n": 10},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"$nor": [{"n": 1}, {"n": 10}]},
        },
        expected={"values": ["b"], "ok": 1.0},
        msg="distinct should support $nor in query",
    ),
    CommandTestCase(
        "query_not",
        docs=[
            {"_id": 1, "x": "a", "n": 1},
            {"_id": 2, "x": "b", "n": 5},
            {"_id": 3, "x": "c", "n": 10},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$not": {"$gt": 5}}},
        },
        expected={"values": ["a", "b"], "ok": 1.0},
        msg="distinct should support $not in query",
    ),
    # Element operators.
    CommandTestCase(
        "query_exists",
        docs=[
            {"_id": 1, "x": "a", "opt": "yes"},
            {"_id": 2, "x": "b"},
            {"_id": 3, "x": "c", "opt": "no"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"opt": {"$exists": True}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $exists in query",
    ),
    CommandTestCase(
        "query_type",
        docs=[
            {"_id": 1, "x": "a", "v": 1},
            {"_id": 2, "x": "b", "v": "str"},
            {"_id": 3, "x": "c", "v": 3},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"v": {"$type": "string"}},
        },
        expected={"values": ["b"], "ok": 1.0},
        msg="distinct should support $type in query",
    ),
    # Array operators.
    CommandTestCase(
        "query_all",
        docs=[
            {"_id": 1, "x": "a", "tags": ["red", "blue"]},
            {"_id": 2, "x": "b", "tags": ["green"]},
            {"_id": 3, "x": "c", "tags": ["red", "green"]},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"tags": {"$all": ["red"]}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $all in query",
    ),
    CommandTestCase(
        "query_elemMatch",
        docs=[
            {"_id": 1, "x": "a", "scores": [{"v": 80}, {"v": 90}]},
            {"_id": 2, "x": "b", "scores": [{"v": 60}, {"v": 70}]},
            {"_id": 3, "x": "c", "scores": [{"v": 95}]},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"scores": {"$elemMatch": {"v": {"$gte": 90}}}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $elemMatch in query",
    ),
    CommandTestCase(
        "query_size",
        docs=[
            {"_id": 1, "x": "a", "tags": ["red", "blue"]},
            {"_id": 2, "x": "b", "tags": ["green"]},
            {"_id": 3, "x": "c", "tags": ["red", "green"]},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"tags": {"$size": 1}},
        },
        expected={"values": ["b"], "ok": 1.0},
        msg="distinct should support $size in query",
    ),
    # Evaluation operators.
    CommandTestCase(
        "query_regex",
        docs=[
            {"_id": 1, "x": "a", "name": "apple"},
            {"_id": 2, "x": "b", "name": "banana"},
            {"_id": 3, "x": "c", "name": "apricot"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"name": {"$regex": "^ap"}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $regex in query",
    ),
    CommandTestCase(
        "query_mod",
        docs=[
            {"_id": 1, "x": "a", "n": 10},
            {"_id": 2, "x": "b", "n": 15},
            {"_id": 3, "x": "c", "n": 20},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"n": {"$mod": [10, 0]}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $mod in query",
    ),
    CommandTestCase(
        "query_expr",
        docs=[
            {"_id": 1, "x": "a", "a": 5, "b": 3},
            {"_id": 2, "x": "b", "a": 2, "b": 7},
            {"_id": 3, "x": "c", "a": 10, "b": 1},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"$expr": {"$gt": ["$a", "$b"]}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $expr in query",
    ),
    # Bitwise operators.
    CommandTestCase(
        "query_bitsAllSet",
        docs=[
            {"_id": 1, "x": "a", "flags": 7},
            {"_id": 2, "x": "b", "flags": 3},
            {"_id": 3, "x": "c", "flags": 5},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"flags": {"$bitsAllSet": 5}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $bitsAllSet in query",
    ),
    CommandTestCase(
        "query_bitsAllClear",
        docs=[
            {"_id": 1, "x": "a", "flags": 7},
            {"_id": 2, "x": "b", "flags": 3},
            {"_id": 3, "x": "c", "flags": 0},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"flags": {"$bitsAllClear": 4}},
        },
        expected={"values": ["b", "c"], "ok": 1.0},
        msg="distinct should support $bitsAllClear in query",
    ),
    CommandTestCase(
        "query_bitsAnySet",
        docs=[
            {"_id": 1, "x": "a", "flags": 7},
            {"_id": 2, "x": "b", "flags": 0},
            {"_id": 3, "x": "c", "flags": 4},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"flags": {"$bitsAnySet": 4}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $bitsAnySet in query",
    ),
    CommandTestCase(
        "query_bitsAnyClear",
        docs=[
            {"_id": 1, "x": "a", "flags": 7},
            {"_id": 2, "x": "b", "flags": 3},
            {"_id": 3, "x": "c", "flags": 5},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"flags": {"$bitsAnyClear": 6}},
        },
        expected={"values": ["b", "c"], "ok": 1.0},
        msg="distinct should support $bitsAnyClear in query",
    ),
    # Geospatial operators.
    CommandTestCase(
        "query_geoWithin",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "x": "a", "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "x": "b", "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.5]}}},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should support $geoWithin in query",
    ),
    CommandTestCase(
        "query_geoIntersects",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "x": "a", "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "x": "b", "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
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
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should support $geoIntersects in query",
    ),
    CommandTestCase(
        "query_near",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "x": "a", "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "x": "b", "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {
                "loc": {
                    "$near": {
                        "$geometry": {"type": "Point", "coordinates": [0, 0]},
                        "$maxDistance": 100000,
                    }
                }
            },
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should support $near in query",
    ),
    CommandTestCase(
        "query_nearSphere",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "x": "a", "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "x": "b", "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {
                "loc": {
                    "$nearSphere": {
                        "$geometry": {"type": "Point", "coordinates": [0, 0]},
                        "$maxDistance": 100000,
                    }
                }
            },
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should support $nearSphere in query",
    ),
    # Schema and scripting operators.
    CommandTestCase(
        "query_jsonSchema",
        docs=[
            {"_id": 1, "x": "a", "name": "hello"},
            {"_id": 2, "x": "b", "name": Int64(123)},
            {"_id": 3, "x": "c"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {
                "$jsonSchema": {
                    "required": ["name"],
                    "properties": {"name": {"bsonType": "string"}},
                }
            },
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should support $jsonSchema in query",
    ),
    CommandTestCase(
        "query_where",
        docs=[
            {"_id": 1, "x": "a", "n": 5},
            {"_id": 2, "x": "b", "n": 15},
            {"_id": 3, "x": "c", "n": 25},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"$where": "this.n > 10"},
        },
        expected={"values": ["b", "c"], "ok": 1.0},
        msg="distinct should support $where in query",
    ),
    # Text search (requires text index).
    CommandTestCase(
        "query_text",
        indexes=[IndexModel([("content", "text")])],
        docs=[
            {"_id": 1, "x": "a", "content": "hello world"},
            {"_id": 2, "x": "b", "content": "foo bar"},
            {"_id": 3, "x": "c", "content": "hello foo"},
        ],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"$text": {"$search": "hello"}},
        },
        expected={"values": ["a", "c"], "ok": 1.0},
        msg="distinct should support $text in query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DISTINCT_QUERY_OPERATOR_TESTS))
def test_distinct_query_operators(
    database_client: Any, collection: Any, test: CommandTestCase
) -> None:
    """Test distinct command query operator wiring."""
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
