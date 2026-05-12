"""Tests for $geoNear distance filtering with maxDistance and minDistance."""

from __future__ import annotations

import pytest
from bson import Int64
from bson.decimal128 import Decimal128
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
)

# Property [Distance Filtering]: maxDistance and minDistance filter documents
# by raw distance with inclusive boundaries, independent of
# distanceMultiplier.
GEONEAR_DISTANCE_FILTERING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "max_distance_inclusive",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": 111_318.84502145034,
                }
            }
        ],
        expected=[
            {
                "_id": 0,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear maxDistance should include documents at exactly the boundary distance",
    ),
    StageTestCase(
        "min_distance_inclusive",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [3, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": 111_318.84502145034,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "dist": 222_637.69004290068,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [3, 0]},
                "dist": 333_956.53506435105,
            },
        ],
        msg="$geoNear minDistance should include documents at exactly the boundary distance",
    ),
    StageTestCase(
        "max_distance_filter_before_multiplier",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": 111_318.84502145034,
                    "distanceMultiplier": 0.001,
                }
            }
        ],
        expected=[
            {
                "_id": 0,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111.31884502145034,
            },
        ],
        msg=(
            "$geoNear maxDistance should filter on raw distance"
            " before distanceMultiplier is applied"
        ),
    ),
    StageTestCase(
        "min_distance_filter_before_multiplier",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": 111_318.84502145034,
                    "distanceMultiplier": 0.001,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111.31884502145034,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "dist": 222.63769004290068,
            },
        ],
        msg=(
            "$geoNear minDistance should filter on raw distance"
            " before distanceMultiplier is applied"
        ),
    ),
    StageTestCase(
        "max_distance_less_than_min_distance",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": 100,
                    "minDistance": 200,
                }
            }
        ],
        expected=[],
        msg="$geoNear with maxDistance less than minDistance should return zero documents",
    ),
    StageTestCase(
        "max_distance_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": FLOAT_INFINITY,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear with maxDistance=+Infinity should return all documents",
    ),
    StageTestCase(
        "max_distance_decimal128_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": DECIMAL128_INFINITY,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear with maxDistance=Decimal128(Infinity) should return all documents",
    ),
    StageTestCase(
        "min_distance_zero",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": 0,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear with minDistance=0 should return all documents",
    ),
    StageTestCase(
        "min_distance_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": FLOAT_INFINITY,
                }
            }
        ],
        expected=[],
        msg="$geoNear with minDistance=+Infinity should return no documents",
    ),
    StageTestCase(
        "min_distance_decimal128_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": DECIMAL128_INFINITY,
                }
            }
        ],
        expected=[],
        msg="$geoNear with minDistance=Decimal128(Infinity) should return no documents",
    ),
    StageTestCase(
        "max_distance_int64",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": Int64(200_000),
                }
            }
        ],
        expected=[
            {
                "_id": 0,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear maxDistance should accept Int64 values",
    ),
    StageTestCase(
        "max_distance_decimal128",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": Decimal128("200000"),
                }
            }
        ],
        expected=[
            {
                "_id": 0,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear maxDistance should accept Decimal128 values",
    ),
    StageTestCase(
        "min_distance_int64",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": Int64(200_000),
                }
            }
        ],
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear minDistance should accept Int64 values",
    ),
    StageTestCase(
        "min_distance_decimal128",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": Decimal128("200000"),
                }
            }
        ],
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear minDistance should accept Decimal128 values",
    ),
]

# Property [Distance Filter Expressions]: maxDistance and minDistance accept
# constant expressions as values.
GEONEAR_DISTANCE_FILTER_EXPRESSION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "max_distance_expression",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": {"$add": [100_000, 11_318.84502145034]},
                }
            }
        ],
        expected=[
            {
                "_id": 0,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear maxDistance should accept a constant expression",
    ),
    StageTestCase(
        "min_distance_expression",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [3, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": {"$add": [100_000, 11_318.84502145034]},
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "dist": 222_637.69004290068,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [3, 0]},
                "dist": 333_956.53506435105,
            },
        ],
        msg="$geoNear minDistance should accept a constant expression",
    ),
]

GEONEAR_DISTANCE_FILTERING_ALL_TESTS = (
    GEONEAR_DISTANCE_FILTERING_TESTS + GEONEAR_DISTANCE_FILTER_EXPRESSION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_DISTANCE_FILTERING_ALL_TESTS))
def test_geoNear_distance_filtering(collection, test_case: StageTestCase):
    """Test $geoNear distance filtering with maxDistance and minDistance."""
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
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
