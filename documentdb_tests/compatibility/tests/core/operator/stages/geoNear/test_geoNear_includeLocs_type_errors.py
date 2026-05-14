"""Tests for $geoNear includeLocs type strictness."""

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
from documentdb_tests.framework.error_codes import GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [includeLocs Type Strictness]: includeLocs rejects all
# non-string types.
GEONEAR_INCLUDE_LOCS_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "include_locs_null",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": None,
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with null should fail",
    ),
    StageTestCase(
        "include_locs_int",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": 42,
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with int should fail",
    ),
    StageTestCase(
        "include_locs_bool",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": True,
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with bool should fail",
    ),
    StageTestCase(
        "include_locs_array",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": ["a"],
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with array should fail",
    ),
    StageTestCase(
        "include_locs_document",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": {"a": 1},
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with document should fail",
    ),
    StageTestCase(
        "include_locs_float",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": 3.14,
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with float should fail",
    ),
    StageTestCase(
        "include_locs_int64",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": Int64(1),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with Int64 should fail",
    ),
    StageTestCase(
        "include_locs_decimal128",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": Decimal128("1"),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with Decimal128 should fail",
    ),
    StageTestCase(
        "include_locs_objectid",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": ObjectId("000000000000000000000001"),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with ObjectId should fail",
    ),
    StageTestCase(
        "include_locs_datetime",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with datetime should fail",
    ),
    StageTestCase(
        "include_locs_timestamp",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": Timestamp(1, 1),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with Timestamp should fail",
    ),
    StageTestCase(
        "include_locs_binary",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": Binary(b"\x01"),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with Binary should fail",
    ),
    StageTestCase(
        "include_locs_regex",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": Regex("^a"),
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_INCLUDE_LOCS_TYPE_ERROR,
        msg="$geoNear includeLocs with Regex should fail",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_INCLUDE_LOCS_TYPE_ERROR_TESTS))
def test_geoNear_includeLocs_type_errors(collection, test_case: StageTestCase):
    """Test $geoNear includeLocs type strictness."""
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
