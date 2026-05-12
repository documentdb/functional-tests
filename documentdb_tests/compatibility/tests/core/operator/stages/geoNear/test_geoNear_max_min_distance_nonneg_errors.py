"""Tests for $geoNear maxDistance/minDistance nonnegative requirement."""

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
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [maxDistance/minDistance Nonnegative Requirement]: negative values
# and NaN for maxDistance or minDistance are rejected.
GEONEAR_MAX_MIN_DISTANCE_NONNEG_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "max_distance_negative",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": -1,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear maxDistance with negative value should fail",
    ),
    StageTestCase(
        "max_distance_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": FLOAT_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear maxDistance with NaN should fail",
    ),
    StageTestCase(
        "max_distance_neg_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": FLOAT_NEGATIVE_INFINITY,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear maxDistance with -Infinity should fail",
    ),
    StageTestCase(
        "min_distance_negative",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": -1,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear minDistance with negative value should fail",
    ),
    StageTestCase(
        "min_distance_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": FLOAT_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear minDistance with NaN should fail",
    ),
    StageTestCase(
        "min_distance_neg_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": FLOAT_NEGATIVE_INFINITY,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear minDistance with -Infinity should fail",
    ),
    StageTestCase(
        "max_distance_decimal128_neg_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": DECIMAL128_NEGATIVE_INFINITY,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear maxDistance with Decimal128(-Infinity) should fail",
    ),
    StageTestCase(
        "min_distance_decimal128_neg_infinity",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": DECIMAL128_NEGATIVE_INFINITY,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear minDistance with Decimal128(-Infinity) should fail",
    ),
    StageTestCase(
        "max_distance_decimal128_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": DECIMAL128_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear maxDistance with Decimal128 NaN should fail",
    ),
    StageTestCase(
        "max_distance_decimal128_negative_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": DECIMAL128_NEGATIVE_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear maxDistance with Decimal128 -NaN should fail",
    ),
    StageTestCase(
        "max_distance_decimal128_negative",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": Decimal128("-1"),
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear maxDistance with negative Decimal128 should fail",
    ),
    StageTestCase(
        "max_distance_int64_negative",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": Int64(-1),
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear maxDistance with negative Int64 should fail",
    ),
    StageTestCase(
        "min_distance_decimal128_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": DECIMAL128_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear minDistance with Decimal128 NaN should fail",
    ),
    StageTestCase(
        "min_distance_decimal128_negative_nan",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": DECIMAL128_NEGATIVE_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear minDistance with Decimal128 -NaN should fail",
    ),
    StageTestCase(
        "min_distance_decimal128_negative",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": Decimal128("-1"),
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear minDistance with negative Decimal128 should fail",
    ),
    StageTestCase(
        "min_distance_int64_negative",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": Int64(-1),
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear minDistance with negative Int64 should fail",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_MAX_MIN_DISTANCE_NONNEG_ERROR_TESTS))
def test_geoNear_max_min_distance_nonneg_errors(collection, test_case: StageTestCase):
    """Test $geoNear maxDistance/minDistance nonnegative requirement."""
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
