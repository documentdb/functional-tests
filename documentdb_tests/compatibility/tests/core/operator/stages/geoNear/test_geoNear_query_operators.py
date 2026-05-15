"""Tests for $geoNear query parameter operator support."""

from __future__ import annotations

import pytest
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO


def _geonear_query(query: dict) -> list[dict]:
    """Build a $geoNear pipeline with the given query filter."""
    return [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [0, 0]},
                "distanceField": "dist",
                "spherical": True,
                "query": query,
            }
        }
    ]


# Property [Query Operator Support]: each query operator functions correctly
# inside the $geoNear query parameter.
GEONEAR_QUERY_OPERATOR_TESTS: list[StageTestCase] = [
    # Comparison operators.
    StageTestCase(
        "query_comparison_eq",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
        ],
        pipeline=_geonear_query({"a": {"$eq": 5}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 5,
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $eq",
    ),
    StageTestCase(
        "query_comparison_ne",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
        ],
        pipeline=_geonear_query({"a": {"$ne": 5}}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": 10,
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $ne",
    ),
    StageTestCase(
        "query_comparison_gt",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "a": 15},
        ],
        pipeline=_geonear_query({"a": {"$gt": 5}}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": 10,
                "dist": 111_318.84502145034,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "a": 15,
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear query should support $gt",
    ),
    StageTestCase(
        "query_comparison_gte",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
        ],
        pipeline=_geonear_query({"a": {"$gte": 10}}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": 10,
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $gte",
    ),
    StageTestCase(
        "query_comparison_lt",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
        ],
        pipeline=_geonear_query({"a": {"$lt": 10}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 5,
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $lt",
    ),
    StageTestCase(
        "query_comparison_lte",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
        ],
        pipeline=_geonear_query({"a": {"$lte": 5}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 5,
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $lte",
    ),
    StageTestCase(
        "query_comparison_in",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "a": 15},
        ],
        pipeline=_geonear_query({"a": {"$in": [5, 15]}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 5,
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "a": 15,
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear query should support $in",
    ),
    StageTestCase(
        "query_comparison_nin",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "a": 15},
        ],
        pipeline=_geonear_query({"a": {"$nin": [5, 15]}}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": 10,
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $nin",
    ),
    # Logical operators.
    StageTestCase(
        "query_logical_and",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5, "b": 1},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10, "b": 1},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "a": 10, "b": 2},
        ],
        pipeline=_geonear_query({"$and": [{"a": 10}, {"b": 1}]}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": 10,
                "b": 1,
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $and",
    ),
    StageTestCase(
        "query_logical_or",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "a": 15},
        ],
        pipeline=_geonear_query({"$or": [{"a": 5}, {"a": 15}]}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 5,
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "a": 15,
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear query should support $or",
    ),
    StageTestCase(
        "query_logical_not",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
        ],
        pipeline=_geonear_query({"a": {"$not": {"$gt": 5}}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 5,
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $not",
    ),
    StageTestCase(
        "query_logical_nor",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "a": 15},
        ],
        pipeline=_geonear_query({"$nor": [{"a": 5}, {"a": 15}]}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": 10,
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $nor",
    ),
    # Element operators.
    StageTestCase(
        "query_element_exists",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=_geonear_query({"a": {"$exists": True}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 5,
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $exists",
    ),
    StageTestCase(
        "query_element_type",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": "hello"},
        ],
        pipeline=_geonear_query({"a": {"$type": "string"}}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": "hello",
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $type",
    ),
    # Evaluation operators.
    StageTestCase(
        "query_evaluation_mod",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 4},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 6},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "a": 10},
        ],
        pipeline=_geonear_query({"a": {"$mod": [3, 1]}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 4,
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "a": 10,
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear query should support $mod",
    ),
    StageTestCase(
        "query_evaluation_regex",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "s": "abc"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "s": "xyz"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "s": "abz"},
        ],
        pipeline=_geonear_query({"s": {"$regex": "^ab"}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "s": "abc",
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "s": "abz",
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear query should support $regex",
    ),
    StageTestCase(
        "query_evaluation_expr",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "a": 10},
        ],
        pipeline=_geonear_query({"$expr": {"$gt": ["$a", 5]}}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": 10,
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $expr",
    ),
    StageTestCase(
        "query_evaluation_jsonschema",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 5},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=_geonear_query(
            {"$jsonSchema": {"required": ["a"], "properties": {"a": {"bsonType": "int"}}}}
        ),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": 5,
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $jsonSchema",
    ),
    # Array operators.
    StageTestCase(
        "query_array_all",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "arr": [1, 2, 3]},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "arr": [1, 3]},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "arr": [2, 3]},
        ],
        pipeline=_geonear_query({"arr": {"$all": [1, 3]}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "arr": [1, 2, 3],
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "arr": [1, 3],
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $all",
    ),
    StageTestCase(
        "query_array_elemmatch",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "arr": [1, 2, 3]},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "arr": [4, 5, 6]},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "arr": [7, 8, 9]},
        ],
        pipeline=_geonear_query({"arr": {"$elemMatch": {"$gte": 7}}}),
        expected=[
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "arr": [7, 8, 9],
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear query should support $elemMatch",
    ),
    StageTestCase(
        "query_array_size",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "arr": [1, 2]},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "arr": [1, 2, 3]},
        ],
        pipeline=_geonear_query({"arr": {"$size": 3}}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "arr": [1, 2, 3],
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $size",
    ),
    # Bitwise operators.
    StageTestCase(
        "query_bitwise_bitsallset",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "flags": 7},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "flags": 3},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "flags": 15},
        ],
        pipeline=_geonear_query({"flags": {"$bitsAllSet": 5}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "flags": 7,
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "flags": 15,
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear query should support $bitsAllSet",
    ),
    StageTestCase(
        "query_bitwise_bitsallclear",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "flags": 7},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "flags": 8},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "flags": 15},
        ],
        pipeline=_geonear_query({"flags": {"$bitsAllClear": 7}}),
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "flags": 8,
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $bitsAllClear",
    ),
    StageTestCase(
        "query_bitwise_bitsanyset",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "flags": 4},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "flags": 8},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "flags": 16},
        ],
        pipeline=_geonear_query({"flags": {"$bitsAnySet": 6}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "flags": 4,
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $bitsAnySet",
    ),
    StageTestCase(
        "query_bitwise_bitsanyclear",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "flags": 7},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "flags": 3},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "flags": 15},
        ],
        pipeline=_geonear_query({"flags": {"$bitsAnyClear": 12}}),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "flags": 7,
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "flags": 3,
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear query should support $bitsAnyClear",
    ),
    # Geospatial operators (non-proximity).
    StageTestCase(
        "query_geo_geowithin",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=_geonear_query(
            {
                "loc": {
                    "$geoWithin": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-1, -1], [0.5, -1], [0.5, 1], [-1, 1], [-1, -1]]],
                        }
                    }
                }
            }
        ),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $geoWithin",
    ),
    StageTestCase(
        "query_geo_geointersects",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=_geonear_query(
            {
                "loc": {
                    "$geoIntersects": {
                        "$geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-1, -1], [0.5, -1], [0.5, 1], [-1, 1], [-1, -1]]],
                        }
                    }
                }
            }
        ),
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear query should support $geoIntersects",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_QUERY_OPERATOR_TESTS))
def test_geoNear_query_operator_cases(collection, test_case: StageTestCase):
    """Test $geoNear query parameter operator support."""
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
    )
