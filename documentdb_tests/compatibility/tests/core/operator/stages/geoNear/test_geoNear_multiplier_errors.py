"""Tests for $geoNear distanceMultiplier type and value errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, ObjectId, Regex, Timestamp
from bson.decimal128 import Decimal128
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [distanceMultiplier Type Rejection]: distanceMultiplier rejects
# all non-numeric types.
GEONEAR_DISTANCE_MULTIPLIER_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_multiplier_null",
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
                    "distanceMultiplier": None,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with null should fail",
    ),
    StageTestCase(
        "distance_multiplier_string",
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
                    "distanceMultiplier": "hello",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with string should fail",
    ),
    StageTestCase(
        "distance_multiplier_bool",
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
                    "distanceMultiplier": True,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with bool should fail",
    ),
    StageTestCase(
        "distance_multiplier_array",
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
                    "distanceMultiplier": [1],
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with array should fail",
    ),
    StageTestCase(
        "distance_multiplier_document",
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
                    "distanceMultiplier": {"a": 1},
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with document should fail",
    ),
    StageTestCase(
        "distance_multiplier_expression",
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
                    "distanceMultiplier": {"$add": [1, 2]},
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with expression should fail",
    ),
    StageTestCase(
        "distance_multiplier_objectid",
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
                    "distanceMultiplier": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with ObjectId should fail",
    ),
    StageTestCase(
        "distance_multiplier_datetime",
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
                    "distanceMultiplier": datetime(2024, 1, 1, tzinfo=timezone.utc),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with datetime should fail",
    ),
    StageTestCase(
        "distance_multiplier_timestamp",
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
                    "distanceMultiplier": Timestamp(1, 1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with Timestamp should fail",
    ),
    StageTestCase(
        "distance_multiplier_binary",
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
                    "distanceMultiplier": Binary(b"\x01"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with Binary should fail",
    ),
    StageTestCase(
        "distance_multiplier_regex",
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
                    "distanceMultiplier": Regex("^a"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear distanceMultiplier with Regex should fail",
    ),
]

# Property [distanceMultiplier Nonnegative Requirement]: negative values
# and NaN for distanceMultiplier are rejected.
GEONEAR_DISTANCE_MULTIPLIER_NONNEG_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_multiplier_nan",
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
                    "distanceMultiplier": FLOAT_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with NaN should fail",
    ),
    StageTestCase(
        "distance_multiplier_negative_nan",
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
                    "distanceMultiplier": FLOAT_NEGATIVE_INFINITY,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with -Infinity should fail",
    ),
    StageTestCase(
        "distance_multiplier_negative_int",
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
                    "distanceMultiplier": -1,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with negative int should fail",
    ),
    StageTestCase(
        "distance_multiplier_negative_float",
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
                    "distanceMultiplier": -1.0,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with negative float should fail",
    ),
    StageTestCase(
        "distance_multiplier_negative_int64",
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
                    "distanceMultiplier": Int64(-1),
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with negative Int64 should fail",
    ),
    StageTestCase(
        "distance_multiplier_negative_decimal128",
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
                    "distanceMultiplier": Decimal128("-1"),
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with negative Decimal128 should fail",
    ),
    StageTestCase(
        "distance_multiplier_decimal128_nan",
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
                    "distanceMultiplier": DECIMAL128_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with Decimal128 NaN should fail",
    ),
    StageTestCase(
        "distance_multiplier_decimal128_negative_nan",
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
                    "distanceMultiplier": DECIMAL128_NEGATIVE_NAN,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with Decimal128 -NaN should fail",
    ),
    StageTestCase(
        "distance_multiplier_decimal128_neg_infinity",
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
                    "distanceMultiplier": DECIMAL128_NEGATIVE_INFINITY,
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear distanceMultiplier with Decimal128 -Infinity should fail",
    ),
]

GEONEAR_MULTIPLIER_ERROR_TESTS = (
    GEONEAR_DISTANCE_MULTIPLIER_TYPE_ERROR_TESTS + GEONEAR_DISTANCE_MULTIPLIER_NONNEG_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_MULTIPLIER_ERROR_TESTS))
def test_geoNear_multiplier_errors(collection, test_case: StageTestCase):
    """Test $geoNear distanceMultiplier type and value errors."""
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
