"""Tests for $geoNear query parameter errors."""

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
    NEAR_NOT_ALLOWED_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Query Type Rejection]: the query parameter rejects all
# non-document types.
GEONEAR_QUERY_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "query_null",
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
                    "query": None,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with null should fail",
    ),
    StageTestCase(
        "query_string",
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
                    "query": "hello",
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with string should fail",
    ),
    StageTestCase(
        "query_int",
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
                    "query": 42,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with int should fail",
    ),
    StageTestCase(
        "query_bool",
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
                    "query": True,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with bool should fail",
    ),
    StageTestCase(
        "query_array",
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
                    "query": [1],
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with array should fail",
    ),
    StageTestCase(
        "query_float",
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
                    "query": 3.14,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with float should fail",
    ),
    StageTestCase(
        "query_int64",
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
                    "query": Int64(1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with Int64 should fail",
    ),
    StageTestCase(
        "query_decimal128",
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
                    "query": Decimal128("1"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with Decimal128 should fail",
    ),
    StageTestCase(
        "query_objectid",
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
                    "query": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with ObjectId should fail",
    ),
    StageTestCase(
        "query_datetime",
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
                    "query": datetime(2024, 1, 1, tzinfo=timezone.utc),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with datetime should fail",
    ),
    StageTestCase(
        "query_timestamp",
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
                    "query": Timestamp(1, 1),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with Timestamp should fail",
    ),
    StageTestCase(
        "query_binary",
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
                    "query": Binary(b"\x01"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with Binary should fail",
    ),
    StageTestCase(
        "query_regex",
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
                    "query": Regex("^a"),
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$geoNear query with Regex should fail",
    ),
]

# Property [Query Near/NearSphere Rejection]: $near and $nearSphere inside
# the query parameter are rejected because they conflict with $geoNear.
GEONEAR_QUERY_NEAR_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "query_near",
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
                    "query": {
                        "loc": {
                            "$near": {
                                "$geometry": {
                                    "type": "Point",
                                    "coordinates": [0, 0],
                                }
                            }
                        }
                    },
                }
            }
        ],
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$geoNear query with $near should fail",
    ),
    StageTestCase(
        "query_near_sphere",
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
                    "query": {
                        "loc": {
                            "$nearSphere": {
                                "$geometry": {
                                    "type": "Point",
                                    "coordinates": [0, 0],
                                }
                            }
                        }
                    },
                }
            }
        ],
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$geoNear query with $nearSphere should fail",
    ),
]

# Property [Query Text/Where Rejection]: $text and $where inside the query
# parameter are rejected because they are not supported in $geoNear queries.
GEONEAR_QUERY_TEXT_WHERE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "query_text",
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
                    "query": {"$text": {"$search": "test"}},
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear query with $text should fail",
    ),
    StageTestCase(
        "query_where",
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
                    "query": {"$where": "true"},
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$geoNear query with $where should fail",
    ),
]

GEONEAR_QUERY_ERROR_TESTS = (
    GEONEAR_QUERY_TYPE_ERROR_TESTS
    + GEONEAR_QUERY_NEAR_ERROR_TESTS
    + GEONEAR_QUERY_TEXT_WHERE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_QUERY_ERROR_TESTS))
def test_geoNear_query_errors(collection, test_case: StageTestCase):
    """Test $geoNear query parameter errors."""
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
