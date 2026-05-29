"""Tests for geospatial index error cases.

Validates invalid GeoJSON data rejection, invalid BSON types in geo fields,
polygon structural errors, 2d out-of-range rejection, missing index errors,
invalid option values, index build on invalid data, index on view, and
invalid aggregation pipeline usage.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    CANNOT_CREATE_INDEX_ERROR,
    CANT_EXTRACT_GEO_KEYS_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    GEO_2D_OUT_OF_RANGE_ERROR,
    GEO_NEAR_NOT_FIRST_STAGE_ERROR,
    INDEX_NOT_FOUND_ERROR,
    INVALID_OPTIONS_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


INVALID_GEOJSON_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="invalid_geojson_type_string",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "InvalidType", "coordinates": [0, 0]}},
        msg="Invalid GeoJSON type should fail on insert",
    ),
    IndexTestCase(
        id="invalid_point_wrong_coords_count",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "Point", "coordinates": [1]}},
        msg="Point with 1 coordinate should fail",
    ),
    IndexTestCase(
        id="invalid_longitude_out_of_range",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "Point", "coordinates": [-181, 0]}},
        msg="Longitude -181 should fail",
    ),
    IndexTestCase(
        id="invalid_latitude_out_of_range",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "Point", "coordinates": [0, 91]}},
        msg="Latitude 91 should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_GEOJSON_TESTS))
def test_geospatial_invalid_data(collection, test):
    """Test 2dsphere index rejects invalid GeoJSON data."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(
        result, {"writeErrors": [{"code": CANT_EXTRACT_GEO_KEYS_ERROR}]}, msg=test.msg
    )


ADDITIONAL_INVALID_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="invalid_longitude_positive_out_of_range",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "Point", "coordinates": [181, 0]}},
        msg="Longitude +181 should fail",
    ),
    IndexTestCase(
        id="invalid_latitude_negative_out_of_range",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "Point", "coordinates": [0, -91]}},
        msg="Latitude -91 should fail",
    ),
    IndexTestCase(
        id="invalid_point_empty_coordinates",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "Point", "coordinates": []}},
        msg="Point with empty coordinates should fail",
    ),
    IndexTestCase(
        id="invalid_bson_string_in_geo_field",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": "hello"},
        msg="String in geo field should fail",
    ),
    IndexTestCase(
        id="invalid_bson_integer_in_geo_field",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": 42},
        msg="Integer in geo field should fail",
    ),
    IndexTestCase(
        id="invalid_bson_boolean_in_geo_field",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": True},
        msg="Boolean in geo field should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADDITIONAL_INVALID_TESTS))
def test_geospatial_additional_invalid_data(collection, test):
    """Test 2dsphere index rejects additional invalid data types and values."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(
        result, {"writeErrors": [{"code": CANT_EXTRACT_GEO_KEYS_ERROR}]}, msg=test.msg
    )


def test_geospatial_near_without_index_fails(collection):
    """Test $near without geospatial index fails."""
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        },
    )
    assertFailureCode(
        result, NO_QUERY_EXECUTION_PLANS_ERROR, msg="$near without geo index should fail"
    )


def test_geospatial_geonear_not_first_stage_fails(collection):
    """Test $geoNear as non-first stage fails."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2ds"}],
        },
    )
    collection.insert_one(
        {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "origin"}
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"name": "origin"}},
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "dist",
                        "spherical": True,
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, GEO_NEAR_NOT_FIRST_STAGE_ERROR, msg="$geoNear must be first stage")


def test_geospatial_polygon_not_closed_fails(collection):
    """Test polygon with first point != last point fails on insert."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2ds"}],
        },
    )
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [
                {
                    "_id": 1,
                    "loc": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
                    },
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": CANT_EXTRACT_GEO_KEYS_ERROR}]},
        msg="Unclosed polygon should fail",
    )


def test_geospatial_polygon_too_few_points_fails(collection):
    """Test polygon with fewer than 4 points fails on insert."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2ds"}],
        },
    )
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [
                {
                    "_id": 1,
                    "loc": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [0, 0]]],
                    },
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": CANT_EXTRACT_GEO_KEYS_ERROR}]},
        msg="Polygon with <4 points should fail",
    )


def test_geospatial_2d_out_of_range_fails(collection):
    """Test 2d index rejects coordinates outside custom min/max bounds."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"loc": "2d"}, "name": "loc_2d", "min": -500, "max": 500}
            ],  # custom range
        },
    )
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "loc": [600, 0]}]},
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": GEO_2D_OUT_OF_RANGE_ERROR}]},
        msg="Coordinates outside min/max should fail",
    )


def test_geospatial_geonear_without_index_fails(collection):
    """Test $geoNear aggregation without geospatial index fails."""
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": [0, 0]},
                        "distanceField": "dist",
                        "spherical": True,
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, INDEX_NOT_FOUND_ERROR, msg="$geoNear without geo index should fail")


INVALID_VERSION_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="2dsphereIndexVersion_zero",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds", "2dsphereIndexVersion": 0},),
        msg="2dsphereIndexVersion=0 should fail",
    ),
    IndexTestCase(
        id="2dsphereIndexVersion_too_high",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds", "2dsphereIndexVersion": 4},),
        msg="2dsphereIndexVersion=4 should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_VERSION_TESTS))
def test_geospatial_invalid_2dsphere_version(collection, test):
    """Test 2dsphere index rejects invalid 2dsphereIndexVersion values."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, CANNOT_CREATE_INDEX_ERROR, msg=test.msg)


INVALID_BITS_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="bits_zero",
        indexes=({"key": {"loc": "2d"}, "name": "loc_2d", "bits": 0},),
        msg="bits=0 should fail",
    ),
    IndexTestCase(
        id="bits_negative",
        indexes=({"key": {"loc": "2d"}, "name": "loc_2d", "bits": -1},),
        msg="bits=-1 should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_BITS_TESTS))
def test_geospatial_invalid_bits(collection, test):
    """Test 2d index rejects invalid bits values."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, INVALID_OPTIONS_ERROR, msg=test.msg)


MISSING_GEOJSON_FIELD_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="missing_type_field",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"coordinates": [0, 0]}},
        msg="GeoJSON missing 'type' field should fail",
    ),
    IndexTestCase(
        id="missing_coordinates_field",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "Point"}},
        msg="GeoJSON missing 'coordinates' field should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MISSING_GEOJSON_FIELD_TESTS))
def test_geospatial_missing_geojson_fields(collection, test):
    """Test 2dsphere index rejects GeoJSON with missing required fields."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(
        result, {"writeErrors": [{"code": CANT_EXTRACT_GEO_KEYS_ERROR}]}, msg=test.msg
    )


ADDITIONAL_GEOJSON_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="lowercase_type_point",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={"_id": 1, "loc": {"type": "point", "coordinates": [0, 0]}},
        msg="Lowercase 'point' type should fail (case-sensitive)",
    ),
    IndexTestCase(
        id="multikey_array_of_geojson",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={
            "_id": 1,
            "loc": [
                {"type": "Point", "coordinates": [0, 0]},
                {"type": "Point", "coordinates": [1, 1]},
            ],
        },
        msg="Array of GeoJSON objects should fail",
    ),
    IndexTestCase(
        id="self_intersecting_polygon_bowtie",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2ds"},),
        input={
            "_id": 1,
            "loc": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [10, 10], [10, 0], [0, 10], [0, 0]]],
            },
        },
        msg="Self-intersecting GeoJSON Polygon (bowtie) ring should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADDITIONAL_GEOJSON_ERROR_TESTS))
def test_geospatial_additional_geojson_errors(collection, test):
    """Test 2dsphere index rejects invalid GeoJSON structures."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(
        result, {"writeErrors": [{"code": CANT_EXTRACT_GEO_KEYS_ERROR}]}, msg=test.msg
    )


def test_geospatial_2d_default_range_out_of_bounds(collection):
    """Test 2d index with default range rejects coordinates outside [-180, 180]."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"loc": "2d"}, "name": "loc_2d"}]},
    )
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "loc": [181, 0]}]},
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"code": GEO_2D_OUT_OF_RANGE_ERROR}]},
        msg="181 exceeds default 2d range",
    )


def test_geospatial_index_build_on_invalid_data(collection):
    """Test creating 2dsphere index fails when collection has invalid geo data."""
    collection.insert_one({"_id": 1, "loc": "not valid geo"})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2ds"}],
        },
    )
    assertFailureCode(
        result, CANT_EXTRACT_GEO_KEYS_ERROR, msg="Index build on invalid data should fail"
    )


def test_geospatial_index_on_view_fails(collection):
    """Test creating geospatial index on a view fails."""
    db = collection.database
    db.drop_collection("geo_view")
    db.command({"create": "geo_view", "viewOn": collection.name, "pipeline": []})
    result = execute_command(
        collection,
        {"createIndexes": "geo_view", "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2ds"}]},
    )
    assertFailureCode(result, COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR, msg="Index on view should fail")
