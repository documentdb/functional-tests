"""Tests for $nearSphere error handling — all error/rejection cases consolidated."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    NEAR_NOT_ALLOWED_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

GEOJSON_TYPE_VALIDATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="type_linestring",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "LineString",
                        "coordinates": [[0, 0], [1, 1]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject GeoJSON type LineString",
    ),
    QueryTestCase(
        id="type_polygon",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject GeoJSON type Polygon",
    ),
    QueryTestCase(
        id="type_multipoint",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "MultiPoint",
                        "coordinates": [[0, 0], [1, 1]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject GeoJSON type MultiPoint",
    ),
    QueryTestCase(
        id="type_multilinestring",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "MultiLineString",
                        "coordinates": [[[0, 0], [1, 1]], [[2, 2], [3, 3]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject GeoJSON type MultiLineString",
    ),
    QueryTestCase(
        id="type_multipolygon",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 0]]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject GeoJSON type MultiPolygon",
    ),
    QueryTestCase(
        id="type_geometrycollection",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "GeometryCollection",
                        "geometries": [{"type": "Point", "coordinates": [0, 0]}],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject GeoJSON type GeometryCollection",
    ),
    QueryTestCase(
        id="type_unknown_string",
        filter={
            "loc": {"$nearSphere": {"$geometry": {"type": "InvalidType", "coordinates": [0, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject unknown geometry type string",
    ),
    QueryTestCase(
        id="type_numeric",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": 123, "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-string type field",
    ),
    QueryTestCase(
        id="type_null",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": None, "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null type field",
    ),
]


INVALID_COORDINATE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="minkey_coordinates",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [{"$minKey": 1}, {"$minKey": 1}]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject MinKey coordinates",
    ),
]


INVALID_GEOMETRY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="missing_coordinates",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry missing coordinates",
    ),
    QueryTestCase(
        id="empty_coordinates",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": []}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty coordinates array",
    ),
    QueryTestCase(
        id="single_coordinate",
        filter={
            "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [-73.9667]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject single coordinate",
    ),
    QueryTestCase(
        id="geometry_null",
        filter={"loc": {"$nearSphere": {"$geometry": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null $geometry",
    ),
]


INVALID_LEGACY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nearSphere_null_value",
        filter={"loc": {"$nearSphere": None}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null value for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_string_value",
        filter={"loc": {"$nearSphere": "invalid"}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject string value for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_numeric_value",
        filter={"loc": {"$nearSphere": 123}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject numeric value for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_boolean_value",
        filter={"loc": {"$nearSphere": True}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject boolean value for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_empty_object",
        filter={"loc": {"$nearSphere": {}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty object for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_single_element_array",
        filter={"loc": {"$nearSphere": [-73.9667]}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject single element array for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_empty_array",
        filter={"loc": {"$nearSphere": []}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty array for $nearSphere",
    ),
]


COORDINATE_BOUNDARY_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_below_neg180",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [-181, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject longitude < -180",
    ),
    QueryTestCase(
        id="longitude_above_180",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [181, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject longitude > 180",
    ),
    QueryTestCase(
        id="latitude_below_neg90",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, -91]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject latitude < -90",
    ),
    QueryTestCase(
        id="latitude_above_90",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 91]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject latitude > 90",
    ),
]


SPECIAL_NUMERIC_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="coordinates_nan",
        filter={
            "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [FLOAT_NAN, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN in coordinates",
    ),
    QueryTestCase(
        id="coordinates_infinity",
        filter={
            "loc": {
                "$nearSphere": {"$geometry": {"type": "Point", "coordinates": [FLOAT_INFINITY, 0]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity in coordinates",
    ),
    QueryTestCase(
        id="coordinates_neg_infinity",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [FLOAT_NEGATIVE_INFINITY, 0]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity in coordinates",
    ),
]

ERROR_TESTS: list[QueryTestCase] = (
    GEOJSON_TYPE_VALIDATION_TESTS
    + INVALID_COORDINATE_TESTS
    + INVALID_GEOMETRY_TESTS
    + INVALID_LEGACY_TESTS
    + COORDINATE_BOUNDARY_ERROR_TESTS
    + SPECIAL_NUMERIC_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_nearSphere_errors(collection, test):
    """Verifies $nearSphere rejects invalid inputs."""
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


OPERATOR_RESTRICTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="two_nearSphere_different_fields",
        filter={
            "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
            "loc2": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [1, 1]}}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject two $nearSphere on different fields",
    ),
    QueryTestCase(
        id="two_nearSphere_inside_and",
        filter={
            "$and": [
                {"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
                {"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [1, 1]}}}},
            ]
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject two $nearSphere inside $and",
    ),
    QueryTestCase(
        id="nearSphere_combined_with_near",
        filter={
            "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
            "loc2": {"$near": {"$geometry": {"type": "Point", "coordinates": [1, 1]}}},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $nearSphere combined with $near",
    ),
    QueryTestCase(
        id="nearSphere_combined_with_text",
        filter={
            "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
            "$text": {"$search": "test"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $nearSphere combined with $text",
    ),
    QueryTestCase(
        id="nearSphere_inside_or",
        filter={
            "$or": [
                {"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
                {"category": "B"},
            ]
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $nearSphere inside $or",
    ),
    QueryTestCase(
        id="nearSphere_inside_nor",
        filter={
            "$nor": [
                {"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
                {"category": "B"},
            ]
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $nearSphere inside $nor",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPERATOR_RESTRICTION_TESTS))
def test_nearSphere_operator_restriction_errors(collection, test):
    """Verifies $nearSphere rejects invalid operator combinations."""
    collection.create_index([("loc", "2dsphere")])
    collection.create_index([("loc2", "2dsphere")])
    # Text index needed for $text test case; no docs with "content" field required
    # because rejection happens at query parse time, not execution time.
    collection.create_index([("content", "text")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


PIPELINE_RESTRICTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nearSphere_in_aggregate_match",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="Should reject $nearSphere in aggregation pipeline $match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PIPELINE_RESTRICTION_TESTS))
def test_nearSphere_pipeline_restriction(collection, test):
    """Verifies $nearSphere is rejected in aggregation pipeline $match."""
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": test.filter}],
            "cursor": {},
        },
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


INDEX_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geojson_without_2dsphere_index",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Should error without 2dsphere index",
    ),
    QueryTestCase(
        id="legacy_without_geo_index",
        filter={"loc": {"$nearSphere": [0, 0]}},
        doc=[{"_id": 1, "loc": [0, 0]}],
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="Should error without geo index",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INDEX_ERROR_TESTS))
def test_nearSphere_index_errors(collection, test):
    """Verifies $nearSphere errors without required geo index."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_nearSphere_after_dropping_index_errors(collection):
    """Verifies $nearSphere errors after dropping the required index."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    collection.drop_index([("loc", "2dsphere")])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
            },
        },
    )
    assertFailureCode(
        result, NO_QUERY_EXECUTION_PLANS_ERROR, msg="Should error after dropping index"
    )
