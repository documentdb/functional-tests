"""Tests for $geoNear distanceMultiplier scaling."""

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
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [distanceMultiplier Scaling]: distanceMultiplier scales the output
# distance field value by the given factor, defaults to 1 when omitted, and
# always produces a double regardless of input numeric type.
GEONEAR_DISTANCE_MULTIPLIER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_multiplier_omitted",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear with distanceMultiplier omitted should leave distances unmodified",
    ),
    StageTestCase(
        "distance_multiplier_scales_output",
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
        msg="$geoNear distanceMultiplier should scale the output distance",
    ),
    StageTestCase(
        "distance_multiplier_negative_zero",
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
                    "distanceMultiplier": DOUBLE_NEGATIVE_ZERO,
                }
            }
        ],
        expected=[
            {
                "_id": 0,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_NEGATIVE_ZERO,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": DOUBLE_NEGATIVE_ZERO,
            },
        ],
        msg="$geoNear distanceMultiplier of -0.0 should produce -0.0 distances",
    ),
    StageTestCase(
        "distance_multiplier_int_produces_double",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "distanceMultiplier": 2,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear distanceMultiplier with int input should produce double output",
    ),
    StageTestCase(
        "distance_multiplier_int64_produces_double",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "distanceMultiplier": Int64(2),
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear distanceMultiplier with Int64 input should produce double output",
    ),
    StageTestCase(
        "distance_multiplier_decimal128_produces_double",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "distanceMultiplier": Decimal128("2"),
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 222_637.69004290068,
            },
        ],
        msg="$geoNear distanceMultiplier with Decimal128 input should produce double output",
    ),
]

# Property [distanceMultiplier Infinity]: distanceMultiplier of +Infinity
# produces Infinity for non-origin documents and NaN for the origin document.
GEONEAR_DISTANCE_MULTIPLIER_INFINITY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_multiplier_infinity",
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
                    "distanceMultiplier": FLOAT_INFINITY,
                }
            }
        ],
        expected=[
            {
                "_id": 0,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": pytest.approx(FLOAT_NAN, nan_ok=True),
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": FLOAT_INFINITY,
            },
        ],
        msg=(
            "$geoNear distanceMultiplier of +Infinity should produce NaN"
            " for origin and Infinity for non-origin"
        ),
    ),
]

GEONEAR_DISTANCE_MULTIPLIER_TESTS_ALL = (
    GEONEAR_DISTANCE_MULTIPLIER_TESTS + GEONEAR_DISTANCE_MULTIPLIER_INFINITY_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_DISTANCE_MULTIPLIER_TESTS_ALL))
def test_geoNear_distance_multiplier(collection, test_case: StageTestCase):
    """Test $geoNear distanceMultiplier scaling."""
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
