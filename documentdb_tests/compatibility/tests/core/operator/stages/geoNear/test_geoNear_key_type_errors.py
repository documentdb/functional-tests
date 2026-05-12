"""Tests for $geoNear key parameter type strictness."""

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

# Property [Key Type Strictness]: the key parameter rejects all non-string
# types and empty string.
GEONEAR_KEY_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "key_null",
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
                    "key": None,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with null should fail",
    ),
    StageTestCase(
        "key_int",
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
                    "key": 42,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with int should fail",
    ),
    StageTestCase(
        "key_bool",
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
                    "key": True,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with bool should fail",
    ),
    StageTestCase(
        "key_array",
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
                    "key": ["a"],
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with array should fail",
    ),
    StageTestCase(
        "key_document",
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
                    "key": {"a": 1},
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with document should fail",
    ),
    StageTestCase(
        "key_empty_string",
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
                    "key": "",
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear key with empty string should fail",
    ),
    StageTestCase(
        "key_float",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": 3.14,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with float should fail",
    ),
    StageTestCase(
        "key_int64",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": Int64(1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with Int64 should fail",
    ),
    StageTestCase(
        "key_decimal128",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": Decimal128("1"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with Decimal128 should fail",
    ),
    StageTestCase(
        "key_objectid",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with ObjectId should fail",
    ),
    StageTestCase(
        "key_datetime",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": datetime(2024, 1, 1, tzinfo=timezone.utc),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with datetime should fail",
    ),
    StageTestCase(
        "key_timestamp",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": Timestamp(1, 1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with Timestamp should fail",
    ),
    StageTestCase(
        "key_binary",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": Binary(b"\x01"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with Binary should fail",
    ),
    StageTestCase(
        "key_regex",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": Regex("^a"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear key with Regex should fail",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_KEY_TYPE_ERROR_TESTS))
def test_geoNear_key_type_errors(collection, test_case: StageTestCase):
    """Test $geoNear key parameter type strictness."""
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
