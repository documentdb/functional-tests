"""Tests for $geoNear maxDistance/minDistance type rejection."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, ObjectId, Regex, Timestamp
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [maxDistance/minDistance Type Rejection]: maxDistance and minDistance
# reject all non-numeric types.
GEONEAR_MAX_MIN_DISTANCE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "max_distance_null",
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
                    "maxDistance": None,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with null should fail",
    ),
    StageTestCase(
        "max_distance_string",
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
                    "maxDistance": "hello",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with string should fail",
    ),
    StageTestCase(
        "max_distance_bool",
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
                    "maxDistance": True,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with bool should fail",
    ),
    StageTestCase(
        "max_distance_array",
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
                    "maxDistance": [1],
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with array should fail",
    ),
    StageTestCase(
        "max_distance_document",
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
                    "maxDistance": {"a": 1},
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with document should fail",
    ),
    StageTestCase(
        "min_distance_null",
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
                    "minDistance": None,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with null should fail",
    ),
    StageTestCase(
        "min_distance_string",
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
                    "minDistance": "hello",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with string should fail",
    ),
    StageTestCase(
        "min_distance_bool",
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
                    "minDistance": True,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with bool should fail",
    ),
    StageTestCase(
        "min_distance_array",
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
                    "minDistance": [1],
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with array should fail",
    ),
    StageTestCase(
        "min_distance_document",
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
                    "minDistance": {"a": 1},
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with document should fail",
    ),
    StageTestCase(
        "max_distance_objectid",
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
                    "maxDistance": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with ObjectId should fail",
    ),
    StageTestCase(
        "max_distance_datetime",
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
                    "maxDistance": datetime(2024, 1, 1, tzinfo=timezone.utc),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with datetime should fail",
    ),
    StageTestCase(
        "max_distance_timestamp",
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
                    "maxDistance": Timestamp(1, 1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with Timestamp should fail",
    ),
    StageTestCase(
        "max_distance_binary",
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
                    "maxDistance": Binary(b"\x01"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with Binary should fail",
    ),
    StageTestCase(
        "max_distance_regex",
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
                    "maxDistance": Regex("^a"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear maxDistance with Regex should fail",
    ),
    StageTestCase(
        "min_distance_objectid",
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
                    "minDistance": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with ObjectId should fail",
    ),
    StageTestCase(
        "min_distance_datetime",
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
                    "minDistance": datetime(2024, 1, 1, tzinfo=timezone.utc),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with datetime should fail",
    ),
    StageTestCase(
        "min_distance_timestamp",
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
                    "minDistance": Timestamp(1, 1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with Timestamp should fail",
    ),
    StageTestCase(
        "min_distance_binary",
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
                    "minDistance": Binary(b"\x01"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with Binary should fail",
    ),
    StageTestCase(
        "min_distance_regex",
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
                    "minDistance": Regex("^a"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear minDistance with Regex should fail",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_MAX_MIN_DISTANCE_TYPE_ERROR_TESTS))
def test_geoNear_max_min_distance_type_errors(collection, test_case: StageTestCase):
    """Test $geoNear maxDistance/minDistance type rejection."""
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
