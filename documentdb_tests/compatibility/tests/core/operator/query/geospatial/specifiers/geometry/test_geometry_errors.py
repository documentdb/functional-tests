"""Tests for $geometry error cases — invalid values, $nearSphere errors,
distance validation, non-Point $near, coordinate boundaries, CRS errors,
invalid type fields, and invalid coordinate types."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- CRS constants ---

STRICT_CRS = {
    "type": "name",
    "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
}

CCW_POLYGON = [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]


# --- Error cases: invalid $geometry values ---

INVALID_GEOMETRY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_value",
        filter={"loc": {"$geoIntersects": {"$geometry": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry: null",
    ),
    QueryTestCase(
        id="string_value",
        filter={"loc": {"$geoIntersects": {"$geometry": "invalid"}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry: string",
    ),
    QueryTestCase(
        id="numeric_value",
        filter={"loc": {"$geoIntersects": {"$geometry": 123}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry: number",
    ),
    QueryTestCase(
        id="boolean_value",
        filter={"loc": {"$geoIntersects": {"$geometry": False}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry: boolean",
    ),
    QueryTestCase(
        id="empty_object",
        filter={"loc": {"$geoIntersects": {"$geometry": {}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry: empty object",
    ),
    QueryTestCase(
        id="missing_type_field",
        filter={"loc": {"$geoIntersects": {"$geometry": {"coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry missing type field",
    ),
    QueryTestCase(
        id="missing_coordinates_field",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry missing coordinates field",
    ),
]


# --- Error cases: invalid $geometry with $nearSphere ---

NEARSPHERE_GEOMETRY_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nearSphere_numeric_value",
        filter={"loc": {"$nearSphere": 5}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject numeric value for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_string_value",
        filter={"loc": {"$nearSphere": "invalid"}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject string value for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_boolean_value",
        filter={"loc": {"$nearSphere": True}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject boolean value for $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_min_max_distance_without_geometry",
        filter={
            "loc": {
                "$nearSphere": {
                    "$maxDistance": 1000,
                    "$minDistance": 100,
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $nearSphere with $minDistance/$maxDistance but no $geometry",
    ),
    QueryTestCase(
        id="nearSphere_geometry_out_of_range_longitude",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [200, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject out-of-range longitude in $nearSphere $geometry",
    ),
    QueryTestCase(
        id="nearSphere_geometry_missing_coordinates",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry Point missing coordinates in $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_geometry_empty_coordinates",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": []}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry Point with empty coordinates in $nearSphere",
    ),
    QueryTestCase(
        id="nearSphere_geometry_polygon_with_maxDistance",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    },
                    "$maxDistance": 1000,
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-Point $geometry in $nearSphere",
    ),
]


# --- Error cases: invalid $minDistance/$maxDistance with $geometry ---

DISTANCE_VALIDATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_geometry_minDistance_nan",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$minDistance": float("nan"),
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN $minDistance with $geometry",
    ),
    QueryTestCase(
        id="near_geometry_maxDistance_nan",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": float("nan"),
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN $maxDistance with $geometry",
    ),
    QueryTestCase(
        id="near_geometry_minDistance_negative_infinity",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$minDistance": float("-inf"),
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity $minDistance with $geometry",
    ),
    QueryTestCase(
        id="near_geometry_maxDistance_negative_infinity",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": float("-inf"),
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity $maxDistance with $geometry",
    ),
    QueryTestCase(
        id="near_geometry_minDistance_infinity",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$minDistance": float("inf"),
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity $minDistance with $geometry",
    ),
    QueryTestCase(
        id="near_geometry_maxDistance_infinity",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": float("inf"),
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity $maxDistance with $geometry",
    ),
]


# --- Error cases: $near with non-Point $geometry ---

NON_POINT_NEAR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="near_geometry_linestring",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {
                        "type": "LineString",
                        "coordinates": [[0, 0], [1, 1]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-Point $geometry (LineString) in $near",
    ),
    QueryTestCase(
        id="near_geometry_polygon",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-Point $geometry (Polygon) in $near",
    ),
    QueryTestCase(
        id="nearSphere_geometry_linestring",
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
        msg="Should reject non-Point $geometry (LineString) in $nearSphere",
    ),
]


# --- Error cases: coordinate boundary violations ---

INVALID_BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_below_negative_180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [-181, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject longitude < -180",
    ),
    QueryTestCase(
        id="longitude_above_180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [181, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject longitude > 180",
    ),
    QueryTestCase(
        id="latitude_below_negative_90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, -91]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject latitude < -90",
    ),
    QueryTestCase(
        id="latitude_above_90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 91]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject latitude > 90",
    ),
    QueryTestCase(
        id="nan_longitude",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [float("nan"), 0]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN longitude",
    ),
    QueryTestCase(
        id="nan_latitude",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, float("nan")]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject NaN latitude",
    ),
    QueryTestCase(
        id="infinity_longitude",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [float("inf"), 0]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Infinity longitude",
    ),
    QueryTestCase(
        id="negative_infinity_latitude",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [0, float("-inf")]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject -Infinity latitude",
    ),
]


# --- Error cases: invalid CRS ---

INVALID_CRS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="crs_with_near",
        filter={
            "loc": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [0, 0],
                        "crs": STRICT_CRS,
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject custom CRS with $near",
    ),
    QueryTestCase(
        id="crs_with_nearSphere",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [0, 0],
                        "crs": STRICT_CRS,
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject custom CRS with $nearSphere",
    ),
    QueryTestCase(
        id="invalid_crs_type",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": CCW_POLYGON,
                        "crs": {
                            "type": "invalid",
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
                        },
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject invalid CRS type",
    ),
    QueryTestCase(
        id="invalid_crs_name",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": CCW_POLYGON,
                        "crs": {"type": "name", "properties": {"name": "invalid"}},
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject invalid CRS name",
    ),
    QueryTestCase(
        id="crs_missing_properties",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": CCW_POLYGON,
                        "crs": {"type": "name"},
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject CRS missing properties field",
    ),
]


# --- Error cases: invalid type field values ---

INVALID_TYPE_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="type_as_number",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": 1, "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject numeric type field",
    ),
    QueryTestCase(
        id="type_as_boolean",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": True, "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject boolean type field",
    ),
    QueryTestCase(
        id="type_as_null",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": None, "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null type field",
    ),
    QueryTestCase(
        id="type_as_array",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": [], "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject array type field",
    ),
    QueryTestCase(
        id="type_invalid_string",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "InvalidType", "coordinates": [0, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject invalid type string",
    ),
    QueryTestCase(
        id="type_empty_string",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "", "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject empty type string",
    ),
    QueryTestCase(
        id="type_lowercase_point",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "point", "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject lowercase 'point' (case sensitive)",
    ),
    QueryTestCase(
        id="type_uppercase_point",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "POINT", "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject uppercase 'POINT' (case sensitive)",
    ),
    QueryTestCase(
        id="type_leading_space",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": " Point", "coordinates": [0, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject type with leading space",
    ),
    QueryTestCase(
        id="type_trailing_space",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point ", "coordinates": [0, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject type with trailing space",
    ),
]


# --- Error cases: invalid coordinate types and structures ---

INVALID_COORDINATE_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="coordinates_as_strings",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": ["10", "20"]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject string coordinates",
    ),
    QueryTestCase(
        id="coordinates_as_booleans",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [True, False]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject boolean coordinates",
    ),
    QueryTestCase(
        id="coordinates_as_nulls",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [None, None]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject null coordinates",
    ),
    QueryTestCase(
        id="coordinates_as_objects",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [{}, {}]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject object coordinates",
    ),
    QueryTestCase(
        id="coordinates_non_array_string",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": "invalid"}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-array coordinates (string)",
    ),
    QueryTestCase(
        id="coordinates_non_array_number",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": 123}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject non-array coordinates (number)",
    ),
    QueryTestCase(
        id="point_empty_coordinates",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": []}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Point with empty coordinates",
    ),
    QueryTestCase(
        id="point_single_coordinate",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [10]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Point with single coordinate",
    ),
    QueryTestCase(
        id="linestring_single_point",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "LineString", "coordinates": [[0, 0]]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject LineString with single point",
    ),
    QueryTestCase(
        id="polygon_not_closed",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Polygon with unclosed ring",
    ),
    QueryTestCase(
        id="polygon_less_than_4_points",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [0, 0]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Polygon with less than 4 points",
    ),
]


ALL_TESTS = (
    INVALID_GEOMETRY_TESTS
    + NEARSPHERE_GEOMETRY_ERROR_TESTS
    + DISTANCE_VALIDATION_TESTS
    + NON_POINT_NEAR_TESTS
    + INVALID_BOUNDARY_TESTS
    + INVALID_CRS_TESTS
    + INVALID_TYPE_FIELD_TESTS
    + INVALID_COORDINATE_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geometry_errors(collection, test):
    """Verifies $geometry rejects invalid values, structures, boundaries,
    CRS configurations, type fields, and coordinate types."""
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
