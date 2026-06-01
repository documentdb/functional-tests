"""Tests for $geometry error cases — invalid values, coordinate boundaries,
CRS errors, invalid type fields, invalid coordinate types, invalid polygon structures,
and malformed geometry structures."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

STRICT_CRS = {
    "type": "name",
    "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
}

CCW_POLYGON = [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]


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
        id="outside_geospatial_context",
        filter={"loc": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry used outside geospatial operator context",
    ),
    QueryTestCase(
        id="missing_coordinates_field",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Should reject $geometry missing coordinates field",
    ),
]


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


INVALID_CRS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="invalid_crs_type",
        filter={
            "loc": {
                "$geoIntersects": {
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
                "$geoIntersects": {
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
                "$geoIntersects": {
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
    QueryTestCase(
        id="crs_missing_type",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": CCW_POLYGON,
                        "crs": {
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"}
                        },
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject CRS missing type field",
    ),
    QueryTestCase(
        id="crs_non_polygon_type",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [0, 0],
                        "crs": STRICT_CRS,
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject custom CRS with non-Polygon type",
    ),
]


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


POLYGON_STRUCTURE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="self_intersecting_polygon",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject self-intersecting polygon (bowtie shape)",
    ),
    QueryTestCase(
        id="hole_touching_exterior",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]],
                            [[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]],
                        ],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject polygon with hole sharing vertex with exterior ring",
    ),
    QueryTestCase(
        id="hole_larger_than_exterior",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                            [[-1, -1], [-1, 2], [2, 2], [2, -1], [-1, -1]],
                        ],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject polygon with hole larger than exterior ring",
    ),
]


MALFORMED_STRUCTURE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="point_nested_array",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [[0, 0]]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Point with nested array coordinates [[0,0]]",
    ),
    QueryTestCase(
        id="polygon_flat_coordinates",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject Polygon with flat coordinates (not nested rings)",
    ),
    QueryTestCase(
        id="linestring_single_element_subarrays",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "LineString", "coordinates": [[0], [1]]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Should reject LineString with single-element sub-arrays",
    ),
]


ALL_TESTS = (
    INVALID_GEOMETRY_TESTS
    + INVALID_BOUNDARY_TESTS
    + INVALID_CRS_TESTS
    + INVALID_TYPE_FIELD_TESTS
    + INVALID_COORDINATE_TYPE_TESTS
    + POLYGON_STRUCTURE_TESTS
    + MALFORMED_STRUCTURE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geometry_errors(collection, test):
    """Verifies $geometry rejects invalid values, structures, boundaries,
    CRS configurations, type fields, and coordinate types."""
    collection.create_index([("loc", "2dsphere")])
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
