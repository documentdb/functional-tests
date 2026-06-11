"""
Tests condition operator support for the $elemMatch projection operator.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Condition Operator Support]: the condition argument accepts comparison,
# logical, element, evaluation, array, bitwise, and geospatial query operators; a
# nested $elemMatch selects the outer element without filtering the inner array.
ELEMMATCH_CONDITION_OPERATOR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "cond_eq",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}, {"x": 10}]}],
        projection={"arr": {"$elemMatch": {"x": {"$eq": 5}}}},
        expected=[{"_id": 1, "arr": [{"x": 5}]}],
        msg="$elemMatch should accept $eq in condition",
    ),
    ProjectionTestCase(
        "cond_ne",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}, {"x": 10}]}],
        projection={"arr": {"$elemMatch": {"x": {"$ne": 1}}}},
        expected=[{"_id": 1, "arr": [{"x": 5}]}],
        msg="$elemMatch should accept $ne in condition",
    ),
    ProjectionTestCase(
        "cond_gt",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}, {"x": 10}]}],
        projection={"arr": {"$elemMatch": {"x": {"$gt": 3}}}},
        expected=[{"_id": 1, "arr": [{"x": 5}]}],
        msg="$elemMatch should accept $gt in condition",
    ),
    ProjectionTestCase(
        "cond_gte",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}, {"x": 10}]}],
        projection={"arr": {"$elemMatch": {"x": {"$gte": 5}}}},
        expected=[{"_id": 1, "arr": [{"x": 5}]}],
        msg="$elemMatch should accept $gte in condition",
    ),
    ProjectionTestCase(
        "cond_lt",
        doc=[{"_id": 1, "arr": [{"x": 10}, {"x": 1}, {"x": 5}]}],
        projection={"arr": {"$elemMatch": {"x": {"$lt": 5}}}},
        expected=[{"_id": 1, "arr": [{"x": 1}]}],
        msg="$elemMatch should accept $lt in condition",
    ),
    ProjectionTestCase(
        "cond_lte",
        doc=[{"_id": 1, "arr": [{"x": 10}, {"x": 5}, {"x": 1}]}],
        projection={"arr": {"$elemMatch": {"x": {"$lte": 5}}}},
        expected=[{"_id": 1, "arr": [{"x": 5}]}],
        msg="$elemMatch should accept $lte in condition",
    ),
    ProjectionTestCase(
        "cond_in",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}, {"x": 10}]}],
        projection={"arr": {"$elemMatch": {"x": {"$in": [5, 10]}}}},
        expected=[{"_id": 1, "arr": [{"x": 5}]}],
        msg="$elemMatch should accept $in in condition",
    ),
    ProjectionTestCase(
        "cond_nin",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}, {"x": 10}]}],
        projection={"arr": {"$elemMatch": {"x": {"$nin": [1, 5]}}}},
        expected=[{"_id": 1, "arr": [{"x": 10}]}],
        msg="$elemMatch should accept $nin in condition",
    ),
    ProjectionTestCase(
        "cond_and",
        doc=[
            {
                "_id": 1,
                "arr": [{"x": 1, "y": "a"}, {"x": 5, "y": "b"}, {"x": 10, "y": "c"}],
            }
        ],
        projection={"arr": {"$elemMatch": {"$and": [{"x": {"$gte": 5}}, {"y": "b"}]}}},
        expected=[{"_id": 1, "arr": [{"x": 5, "y": "b"}]}],
        msg="$elemMatch should accept $and in condition",
    ),
    ProjectionTestCase(
        "cond_or",
        doc=[
            {
                "_id": 1,
                "arr": [{"x": 5, "y": "b"}, {"x": 10, "y": "c"}, {"x": 1, "y": "a"}],
            }
        ],
        projection={"arr": {"$elemMatch": {"$or": [{"x": 1}, {"x": 10}]}}},
        expected=[{"_id": 1, "arr": [{"x": 10, "y": "c"}]}],
        msg="$elemMatch should accept $or in condition",
    ),
    ProjectionTestCase(
        "cond_nor",
        doc=[
            {
                "_id": 1,
                "arr": [{"x": 1, "y": "a"}, {"x": 5, "y": "b"}, {"x": 10, "y": "c"}],
            }
        ],
        projection={"arr": {"$elemMatch": {"$nor": [{"x": 1}, {"x": 5}]}}},
        expected=[{"_id": 1, "arr": [{"x": 10, "y": "c"}]}],
        msg="$elemMatch should accept $nor in condition",
    ),
    ProjectionTestCase(
        "cond_not",
        doc=[
            {
                "_id": 1,
                "arr": [{"x": 10, "y": "c"}, {"x": 5, "y": "b"}, {"x": 1, "y": "a"}],
            }
        ],
        projection={"arr": {"$elemMatch": {"x": {"$not": {"$gt": 5}}}}},
        expected=[{"_id": 1, "arr": [{"x": 5, "y": "b"}]}],
        msg="$elemMatch should accept $not in condition",
    ),
    ProjectionTestCase(
        "cond_exists_true",
        doc=[{"_id": 1, "arr": [{"y": "hello"}, {"x": 1}, {"x": None}]}],
        projection={"arr": {"$elemMatch": {"x": {"$exists": True}}}},
        expected=[{"_id": 1, "arr": [{"x": 1}]}],
        msg="$elemMatch should accept $exists: true in condition",
    ),
    ProjectionTestCase(
        "cond_type",
        doc=[{"_id": 1, "arr": [{"x": "hello"}, {"x": None}, {"x": 1}]}],
        projection={"arr": {"$elemMatch": {"x": {"$type": "int"}}}},
        expected=[{"_id": 1, "arr": [{"x": 1}]}],
        msg="$elemMatch should accept $type in condition",
    ),
    ProjectionTestCase(
        "cond_mod",
        doc=[{"_id": 1, "arr": [{"x": 11}, {"x": 12}, {"x": 10}, {"x": 15}]}],
        projection={"arr": {"$elemMatch": {"x": {"$mod": [5, 0]}}}},
        expected=[{"_id": 1, "arr": [{"x": 10}]}],
        msg="$elemMatch should accept $mod in condition",
    ),
    ProjectionTestCase(
        "cond_regex",
        doc=[{"_id": 1, "arr": [{"name": "abc"}, {"name": "xyz"}, {"name": "axyz"}]}],
        projection={"arr": {"$elemMatch": {"name": {"$regex": "^x"}}}},
        expected=[{"_id": 1, "arr": [{"name": "xyz"}]}],
        msg="$elemMatch should accept $regex in condition",
    ),
    ProjectionTestCase(
        "cond_all",
        doc=[
            {
                "_id": 1,
                "arr": [
                    {"tags": ["x", "y"]},
                    {"tags": ["a", "x", "z"]},
                    {"tags": ["a", "b", "c"]},
                ],
            }
        ],
        projection={"arr": {"$elemMatch": {"tags": {"$all": ["a", "b"]}}}},
        expected=[{"_id": 1, "arr": [{"tags": ["a", "b", "c"]}]}],
        msg="$elemMatch should accept $all in condition",
    ),
    ProjectionTestCase(
        "cond_size",
        doc=[
            {
                "_id": 1,
                "arr": [
                    {"tags": ["a", "b", "c"]},
                    {"tags": ["x", "y"]},
                    {"tags": ["a", "x", "z"]},
                ],
            }
        ],
        projection={"arr": {"$elemMatch": {"tags": {"$size": 2}}}},
        expected=[{"_id": 1, "arr": [{"tags": ["x", "y"]}]}],
        msg="$elemMatch should accept $size in condition",
    ),
    ProjectionTestCase(
        "cond_nested_elemmatch_selects_without_filtering_inner",
        doc=[
            {
                "_id": 1,
                "arr": [
                    {"scores": [1, 2, 3]},
                    {"scores": [10, 20, 30]},
                    {"scores": [5, 6, 7]},
                ],
            }
        ],
        projection={"arr": {"$elemMatch": {"scores": {"$elemMatch": {"$gte": 10}}}}},
        expected=[{"_id": 1, "arr": [{"scores": [10, 20, 30]}]}],
        msg="$elemMatch nested condition should select outer element without filtering inner",
    ),
    ProjectionTestCase(
        "cond_bits_all_set",
        doc=[{"_id": 1, "arr": [{"flags": 0b1010}, {"flags": 0b1111}, {"flags": 0b0001}]}],
        projection={"arr": {"$elemMatch": {"flags": {"$bitsAllSet": [0, 1]}}}},
        expected=[{"_id": 1, "arr": [{"flags": 0b1111}]}],
        msg="$elemMatch should accept $bitsAllSet in condition",
    ),
    ProjectionTestCase(
        "cond_bits_any_set",
        doc=[{"_id": 1, "arr": [{"flags": 0b1010}, {"flags": 0b1111}, {"flags": 0b0001}]}],
        projection={"arr": {"$elemMatch": {"flags": {"$bitsAnySet": [0]}}}},
        expected=[{"_id": 1, "arr": [{"flags": 0b1111}]}],
        msg="$elemMatch should accept $bitsAnySet in condition",
    ),
    ProjectionTestCase(
        "cond_bits_all_clear",
        doc=[{"_id": 1, "arr": [{"flags": 0b1111}, {"flags": 0b0001}, {"flags": 0b1010}]}],
        projection={"arr": {"$elemMatch": {"flags": {"$bitsAllClear": [0, 2]}}}},
        expected=[{"_id": 1, "arr": [{"flags": 0b1010}]}],
        msg="$elemMatch should accept $bitsAllClear in condition",
    ),
    ProjectionTestCase(
        "cond_bits_any_clear",
        doc=[{"_id": 1, "arr": [{"flags": 0b1111}, {"flags": 0b0001}, {"flags": 0b1010}]}],
        projection={"arr": {"$elemMatch": {"flags": {"$bitsAnyClear": [0]}}}},
        expected=[{"_id": 1, "arr": [{"flags": 0b1010}]}],
        msg="$elemMatch should accept $bitsAnyClear in condition",
    ),
    ProjectionTestCase(
        "cond_geo_within",
        doc=[
            {
                "_id": 1,
                "places": [
                    {"loc": {"type": "Point", "coordinates": [40, 40]}},
                    {"loc": {"type": "Point", "coordinates": [0, 0]}},
                ],
            }
        ],
        projection={
            "places": {"$elemMatch": {"loc": {"$geoWithin": {"$centerSphere": [[0, 0], 0.01]}}}}
        },
        expected=[{"_id": 1, "places": [{"loc": {"type": "Point", "coordinates": [0, 0]}}]}],
        msg="$elemMatch should accept $geoWithin in condition",
    ),
    ProjectionTestCase(
        "cond_geo_intersects",
        doc=[
            {
                "_id": 1,
                "places": [
                    {"loc": {"type": "Point", "coordinates": [0, 0]}},
                    {"loc": {"type": "Point", "coordinates": [40, 40]}},
                ],
            }
        ],
        projection={
            "places": {
                "$elemMatch": {
                    "loc": {
                        "$geoIntersects": {
                            "$geometry": {
                                "type": "Polygon",
                                "coordinates": [[[39, 39], [41, 39], [41, 41], [39, 41], [39, 39]]],
                            }
                        }
                    }
                }
            }
        },
        expected=[{"_id": 1, "places": [{"loc": {"type": "Point", "coordinates": [40, 40]}}]}],
        msg="$elemMatch should accept $geoIntersects in condition",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ELEMMATCH_CONDITION_OPERATOR_TESTS))
def test_elemmatch_condition_operators(collection, test):
    """Test $elemMatch projection condition operator cases."""
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "projection": test.projection,
    }
    if test.filter is not None:
        cmd["filter"] = test.filter
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
