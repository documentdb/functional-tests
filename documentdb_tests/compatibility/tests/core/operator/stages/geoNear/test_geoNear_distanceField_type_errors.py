"""Tests for $geoNear distanceField type strictness."""

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
from documentdb_tests.framework.error_codes import GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [distanceField Type Strictness]: distanceField rejects all
# non-string types.
GEONEAR_DISTANCE_FIELD_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_field_null",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": None,
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with null should fail",
    ),
    StageTestCase(
        "distance_field_int",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": 42,
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with int should fail",
    ),
    StageTestCase(
        "distance_field_bool",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": True,
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with bool should fail",
    ),
    StageTestCase(
        "distance_field_array",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": ["a"],
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with array should fail",
    ),
    StageTestCase(
        "distance_field_document",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": {"a": 1},
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with document should fail",
    ),
    StageTestCase(
        "distance_field_float",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": 3.14,
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with float should fail",
    ),
    StageTestCase(
        "distance_field_int64",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": Int64(1),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with Int64 should fail",
    ),
    StageTestCase(
        "distance_field_decimal128",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": Decimal128("1"),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with Decimal128 should fail",
    ),
    StageTestCase(
        "distance_field_objectid",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": ObjectId("000000000000000000000001"),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with ObjectId should fail",
    ),
    StageTestCase(
        "distance_field_datetime",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with datetime should fail",
    ),
    StageTestCase(
        "distance_field_timestamp",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": Timestamp(1, 1),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with Timestamp should fail",
    ),
    StageTestCase(
        "distance_field_binary",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": Binary(b"\x01"),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with Binary should fail",
    ),
    StageTestCase(
        "distance_field_regex",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": Regex("^a"),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_DISTANCE_FIELD_TYPE_ERROR,
        msg="$geoNear distanceField with Regex should fail",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_DISTANCE_FIELD_TYPE_ERROR_TESTS))
def test_geoNear_distanceField_type_errors(collection, test_case: StageTestCase):
    """Test $geoNear distanceField type strictness."""
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
