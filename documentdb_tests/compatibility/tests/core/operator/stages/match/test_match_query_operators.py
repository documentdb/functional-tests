"""Tests for $match query operator categories."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Query Operator Support]: each query operator functions correctly
# inside $match as a container.
MATCH_QUERY_OPERATOR_TESTS: list[StageTestCase] = [
    # Comparison operators.
    StageTestCase(
        "query_comparison_eq",
        docs=[{"_id": 1, "a": 5}, {"_id": 2, "a": 10}],
        pipeline=[{"$match": {"a": {"$eq": 5}}}],
        expected=[{"_id": 1, "a": 5}],
        msg="$match should support $eq",
    ),
    StageTestCase(
        "query_comparison_ne",
        docs=[{"_id": 1, "a": 5}, {"_id": 2, "a": 10}],
        pipeline=[{"$match": {"a": {"$ne": 5}}}],
        expected=[{"_id": 2, "a": 10}],
        msg="$match should support $ne",
    ),
    StageTestCase(
        "query_comparison_gt",
        docs=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 10},
        ],
        pipeline=[{"$match": {"a": {"$gt": 5}}}],
        expected=[{"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        msg="$match should support $gt",
    ),
    StageTestCase(
        "query_comparison_gte",
        docs=[{"_id": 1, "a": 3}, {"_id": 2, "a": 5}, {"_id": 3, "a": 10}],
        pipeline=[{"$match": {"a": {"$gte": 5}}}],
        expected=[{"_id": 2, "a": 5}, {"_id": 3, "a": 10}],
        msg="$match should support $gte",
    ),
    StageTestCase(
        "query_comparison_lt",
        docs=[{"_id": 1, "a": 3}, {"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        pipeline=[{"$match": {"a": {"$lt": 5}}}],
        expected=[{"_id": 1, "a": 3}],
        msg="$match should support $lt",
    ),
    StageTestCase(
        "query_comparison_lte",
        docs=[{"_id": 1, "a": 3}, {"_id": 2, "a": 5}, {"_id": 3, "a": 10}],
        pipeline=[{"$match": {"a": {"$lte": 5}}}],
        expected=[{"_id": 1, "a": 3}, {"_id": 2, "a": 5}],
        msg="$match should support $lte",
    ),
    StageTestCase(
        "query_comparison_in",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        pipeline=[{"$match": {"a": {"$in": [1, 3]}}}],
        expected=[{"_id": 1, "a": 1}, {"_id": 3, "a": 3}],
        msg="$match should support $in",
    ),
    StageTestCase(
        "query_comparison_nin",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        pipeline=[{"$match": {"a": {"$nin": [1, 3]}}}],
        expected=[{"_id": 2, "a": 2}],
        msg="$match should support $nin",
    ),
    # Logical operators.
    StageTestCase(
        "query_logical_and",
        docs=[
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 2, "b": 20},
            {"_id": 3, "a": 1, "b": 20},
        ],
        pipeline=[{"$match": {"$and": [{"a": 1}, {"b": {"$gte": 10}}]}}],
        expected=[
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 3, "a": 1, "b": 20},
        ],
        msg="$match should support $and",
    ),
    StageTestCase(
        "query_logical_or",
        docs=[
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 2, "b": 20},
            {"_id": 3, "a": 3, "b": 30},
        ],
        pipeline=[{"$match": {"$or": [{"a": 1}, {"b": 30}]}}],
        expected=[
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 3, "a": 3, "b": 30},
        ],
        msg="$match should support $or",
    ),
    StageTestCase(
        "query_logical_not",
        docs=[{"_id": 1, "a": 3}, {"_id": 2, "a": 7}, {"_id": 3, "a": 10}],
        pipeline=[{"$match": {"a": {"$not": {"$gt": 5}}}}],
        expected=[{"_id": 1, "a": 3}],
        msg="$match should support $not",
    ),
    StageTestCase(
        "query_logical_nor",
        docs=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": 2},
            {"_id": 3, "a": 3},
        ],
        pipeline=[{"$match": {"$nor": [{"a": 1}, {"a": 3}]}}],
        expected=[{"_id": 2, "a": 2}],
        msg="$match should support $nor",
    ),
    # Data type operators.
    StageTestCase(
        "query_datatype_exists",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "b": 20}, {"_id": 3, "a": 30}],
        pipeline=[{"$match": {"a": {"$exists": True}}}],
        expected=[{"_id": 1, "a": 10}, {"_id": 3, "a": 30}],
        msg="$match should support $exists",
    ),
    StageTestCase(
        "query_datatype_type",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": "hello"}, {"_id": 3, "a": 3.14}],
        pipeline=[{"$match": {"a": {"$type": "string"}}}],
        expected=[{"_id": 2, "a": "hello"}],
        msg="$match should support $type",
    ),
    # Miscellaneous operators.
    StageTestCase(
        "query_misc_expr",
        docs=[
            {"_id": 1, "a": 10, "b": 10},
            {"_id": 2, "a": 20, "b": 30},
            {"_id": 3, "a": 5, "b": 5},
        ],
        pipeline=[{"$match": {"$expr": {"$eq": ["$a", "$b"]}}}],
        expected=[
            {"_id": 1, "a": 10, "b": 10},
            {"_id": 3, "a": 5, "b": 5},
        ],
        msg="$match should support $expr",
    ),
    StageTestCase(
        "query_misc_jsonschema",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": "hello"}, {"_id": 3}],
        pipeline=[
            {
                "$match": {
                    "$jsonSchema": {"required": ["a"], "properties": {"a": {"bsonType": "int"}}}
                }
            }
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$match should support $jsonSchema",
    ),
    StageTestCase(
        "query_misc_mod",
        docs=[{"_id": 1, "a": 4}, {"_id": 2, "a": 6}, {"_id": 3, "a": 10}],
        pipeline=[{"$match": {"a": {"$mod": [3, 1]}}}],
        expected=[{"_id": 1, "a": 4}, {"_id": 3, "a": 10}],
        msg="$match should support $mod",
    ),
    StageTestCase(
        "query_misc_regex",
        docs=[{"_id": 1, "s": "abc"}, {"_id": 2, "s": "xyz"}, {"_id": 3, "s": "abz"}],
        pipeline=[{"$match": {"s": {"$regex": "^ab"}}}],
        expected=[{"_id": 1, "s": "abc"}, {"_id": 3, "s": "abz"}],
        msg="$match should support $regex",
    ),
    # Array operators.
    StageTestCase(
        "query_array_all",
        docs=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [1, 3]},
            {"_id": 3, "arr": [2, 3]},
        ],
        pipeline=[{"$match": {"arr": {"$all": [1, 3]}}}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 2, "arr": [1, 3]}],
        msg="$match should support $all",
    ),
    StageTestCase(
        "query_array_elemmatch",
        docs=[
            {"_id": 1, "arr": [0.5, 0.8, 0.95]},
            {"_id": 2, "arr": [0.1, 0.3]},
            {"_id": 3, "arr": [0.9, 1.0]},
        ],
        pipeline=[{"$match": {"arr": {"$elemMatch": {"$gte": 0.9}}}}],
        expected=[
            {"_id": 1, "arr": [0.5, 0.8, 0.95]},
            {"_id": 3, "arr": [0.9, 1.0]},
        ],
        msg="$match should support $elemMatch",
    ),
    StageTestCase(
        "query_array_size",
        docs=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [1]},
            {"_id": 3, "arr": [1, 2]},
        ],
        pipeline=[{"$match": {"arr": {"$size": 2}}}],
        expected=[{"_id": 3, "arr": [1, 2]}],
        msg="$match should support $size",
    ),
    # Bitwise operators.
    StageTestCase(
        "query_bitwise_bitsallclear",
        docs=[
            {"_id": 1, "flags": 7},
            {"_id": 2, "flags": 8},
            {"_id": 3, "flags": 15},
        ],
        # Bitmask 7 (binary 0111): flags 8 (1000) has all bits clear.
        pipeline=[{"$match": {"flags": {"$bitsAllClear": 7}}}],
        expected=[{"_id": 2, "flags": 8}],
        msg="$match should support $bitsAllClear",
    ),
    StageTestCase(
        "query_bitwise_bitsallset",
        docs=[
            {"_id": 1, "flags": 7},
            {"_id": 2, "flags": 3},
            {"_id": 3, "flags": 15},
        ],
        # Bitmask 5 (binary 0101): flags 7 (0111) and 15 (1111) match.
        pipeline=[{"$match": {"flags": {"$bitsAllSet": 5}}}],
        expected=[{"_id": 1, "flags": 7}, {"_id": 3, "flags": 15}],
        msg="$match should support $bitsAllSet",
    ),
    StageTestCase(
        "query_bitwise_bitsanyclear",
        docs=[
            {"_id": 1, "flags": 7},
            {"_id": 2, "flags": 3},
            {"_id": 3, "flags": 15},
        ],
        # Bitmask 12 (binary 1100): flags 7 (0111) and 3 (0011) have at least one clear.
        pipeline=[{"$match": {"flags": {"$bitsAnyClear": 12}}}],
        expected=[{"_id": 1, "flags": 7}, {"_id": 2, "flags": 3}],
        msg="$match should support $bitsAnyClear",
    ),
    StageTestCase(
        "query_bitwise_bitsanyset",
        docs=[
            {"_id": 1, "flags": 4},
            {"_id": 2, "flags": 8},
            {"_id": 3, "flags": 16},
        ],
        # Bitmask 6 (binary 0110): flags 4 (0100) has bit 2 set.
        pipeline=[{"$match": {"flags": {"$bitsAnySet": 6}}}],
        expected=[{"_id": 1, "flags": 4}],
        msg="$match should support $bitsAnySet",
    ),
    # Geospatial operators.
    StageTestCase(
        "query_geo_geointersects",
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        pipeline=[
            {
                "$match": {
                    "loc": {
                        "$geoIntersects": {
                            "$geometry": {
                                "type": "Polygon",
                                "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                            }
                        }
                    }
                }
            }
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="$match should support $geoIntersects",
    ),
    StageTestCase(
        "query_geo_geowithin",
        docs=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [50, 50]},
            {"_id": 3, "loc": [1, 1]},
        ],
        pipeline=[{"$match": {"loc": {"$geoWithin": {"$center": [[0, 0], 10]}}}}],
        expected=[{"_id": 1, "loc": [0, 0]}, {"_id": 3, "loc": [1, 1]}],
        msg="$match should support $geoWithin",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MATCH_QUERY_OPERATOR_TESTS))
def test_match_query_operator_cases(collection, test_case: StageTestCase):
    """Test $match query operator categories."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
