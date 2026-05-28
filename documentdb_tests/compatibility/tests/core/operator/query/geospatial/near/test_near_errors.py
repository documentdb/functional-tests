"""Tests for $near error handling — invalid coordinates, GeoJSON structure, restrictions."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CANNOT_MIX_GEO_WITH_OTHER_OP_ERROR,
    NEAR_NOT_ALLOWED_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

pytestmark = pytest.mark.usefixtures("geo_2dsphere")


COORDINATE_BOUNDARY_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_below_neg180",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [-180.1, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject longitude < -180",
    ),
    QueryTestCase(
        id="longitude_above_180",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [180.1, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject longitude > 180",
    ),
    QueryTestCase(
        id="latitude_below_neg90",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, -90.1]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject latitude < -90",
    ),
    QueryTestCase(
        id="latitude_above_90",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 90.1]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject latitude > 90",
    ),
    QueryTestCase(
        id="coordinates_nan",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [FLOAT_NAN, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN coordinate",
    ),
    QueryTestCase(
        id="coordinates_infinity",
        filter={
            "loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [FLOAT_INFINITY, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity coordinate",
    ),
    QueryTestCase(
        id="coordinates_neg_infinity",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [FLOAT_NEGATIVE_INFINITY, 0]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity coordinate",
    ),
]


GEOJSON_STRUCTURE_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="invalid_type_linestring",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {
                        "type": "LineString",
                        "coordinates": [[-73.9667, 40.78], [-73.9, 40.7]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject LineString geometry type",
    ),
    QueryTestCase(
        id="invalid_type_polygon",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-73.9, 40.7], [-73.9, 40.8], [-74.0, 40.8], [-73.9, 40.7]]
                        ],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Polygon geometry type",
    ),
    QueryTestCase(
        id="invalid_type_multipoint",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {
                        "type": "MultiPoint",
                        "coordinates": [[-73.9667, 40.78], [-73.9, 40.7]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject MultiPoint geometry type",
    ),
    QueryTestCase(
        id="missing_coordinates",
        filter={"loc": {"$near": {"$geometry": {"type": "Point"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry missing coordinates",
    ),
    QueryTestCase(
        id="empty_coordinates",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": []}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty coordinates array",
    ),
    QueryTestCase(
        id="single_coordinate",
        filter={"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [-73.9667]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject single coordinate",
    ),
    QueryTestCase(
        id="null_geometry",
        filter={"loc": {"$near": {"$geometry": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null $geometry",
    ),
    QueryTestCase(
        id="string_geometry",
        filter={"loc": {"$near": {"$geometry": "invalid"}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject string $geometry",
    ),
    QueryTestCase(
        id="unknown_key_in_near",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$unknownKey": 5,
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject unknown keys inside $near",
    ),
]


ALL_ERROR_TESTS = COORDINATE_BOUNDARY_ERROR_TESTS + GEOJSON_STRUCTURE_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_near_errors(collection, test):
    """Verifies $near rejects invalid inputs."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


RESTRICTION_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_without_geometry",
        filter={"loc": {"$near": {}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $near with empty object (no $geometry)",
    ),
    QueryTestCase(
        id="near_and_nearSphere_same_field",
        filter={
            "loc": {
                "$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
                "$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $near and $nearSphere on same field",
    ),
    QueryTestCase(
        id="near_and_nearSphere_different_fields",
        filter={
            "loc1": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
            "loc2": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $near and $nearSphere on different fields",
    ),
    QueryTestCase(
        id="near_inside_or",
        filter={
            "$or": [
                {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
                {"name": "test"},
            ]
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $near inside $or",
    ),
    QueryTestCase(
        id="near_inside_nor",
        filter={
            "$nor": [{"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}}]
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $near inside $nor",
    ),
    QueryTestCase(
        id="near_inside_not",
        filter={
            "$and": [
                {
                    "loc": {
                        "$not": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
                    }
                }
            ]
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $near inside $not",
    ),
    QueryTestCase(
        id="near_inside_elemMatch",
        filter={
            "arr": {
                "$elemMatch": {
                    "loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $near inside $elemMatch",
    ),
    QueryTestCase(
        id="two_near_different_fields",
        filter={
            "loc1": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
            "loc2": {"$near": {"$geometry": {"type": "Point", "coordinates": [1, 1]}}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject two $near on different fields",
    ),
    QueryTestCase(
        id="two_near_inside_and",
        filter={
            "$and": [
                {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
                {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [1, 1]}}}},
            ]
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject two $near inside $and",
    ),
    QueryTestCase(
        id="near_combined_with_other_op_same_field",
        filter={
            "loc": {
                "$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
                "$eq": {"type": "Point", "coordinates": [0, 0]},
            }
        },
        error_code=CANNOT_MIX_GEO_WITH_OTHER_OP_ERROR,
        msg="Should reject $near combined with $eq on same field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESTRICTION_ERROR_TESTS))
def test_near_restriction_errors(collection, test):
    """Verifies $near rejects invalid operator combinations."""
    collection.create_index([("loc1", "2dsphere")])
    collection.create_index([("loc2", "2dsphere")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_near_in_aggregate_match_errors(collection):
    """Verifies $near is not permitted in aggregation pipeline $match (parse-time rejection)."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$match": {
                        "loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, NEAR_NOT_ALLOWED_ERROR, msg="Should reject $near in aggregate $match")


def test_near_combined_with_text_errors(collection):
    """Verifies $near cannot be combined with $text in the same query."""
    collection.create_index([("name", "text")])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
                "$text": {"$search": "test"},
            },
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Should reject $near combined with $text")


def test_near_on_timeseries_errors(database_client):
    """Verifies $near is not allowed on timeseries collections."""
    db = database_client
    db.create_collection("ts_coll", timeseries={"timeField": "ts", "metaField": "meta"})
    coll = db["ts_coll"]
    result = execute_command(
        coll,
        {
            "find": "ts_coll",
            "filter": {
                "meta.loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
            },
        },
    )
    assertFailureCode(
        result, NEAR_NOT_ALLOWED_ERROR, msg="Should reject $near on timeseries collection"
    )
