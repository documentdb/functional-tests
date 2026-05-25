"""
Tests for $geoWithin error cases — argument validation, coordinate validation,
invalid geometry, CRS validation, and legacy shape specifier validation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

GEOJSON_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="missing_geometry_and_shape",
        filter={"loc": {"$geoWithin": {}}},
        error_code=BAD_VALUE_ERROR,
        msg="Missing $geometry and no shape operator should error",
    ),
    QueryTestCase(
        id="invalid_geometry_type_linestring",
        filter={
            "loc": {
                "$geoWithin": {"$geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid geometry type LineString should error",
    ),
    QueryTestCase(
        id="empty_coordinates",
        filter={"loc": {"$geoWithin": {"$geometry": {"type": "Polygon", "coordinates": []}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty coordinates array should error",
    ),
    QueryTestCase(
        id="non_array_coordinates",
        filter={
            "loc": {"$geoWithin": {"$geometry": {"type": "Polygon", "coordinates": "invalid"}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Non-array coordinates should error",
    ),
    QueryTestCase(
        id="non_object_argument",
        filter={"loc": {"$geoWithin": "invalid"}},
        error_code=BAD_VALUE_ERROR,
        msg="Non-object argument should error",
    ),
    QueryTestCase(
        id="null_argument",
        filter={"loc": {"$geoWithin": None}},
        error_code=BAD_VALUE_ERROR,
        msg="Null argument should error",
    ),
    QueryTestCase(
        id="latitude_above_90",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 91], [1, 91], [1, 92], [0, 92], [0, 91]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Latitude > 90 should error",
    ),
    QueryTestCase(
        id="self_intersecting_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [2, 2], [2, 0], [0, 2], [0, 0]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Self-intersecting polygon should error",
    ),
    QueryTestCase(
        id="unclosed_polygon_ring",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Unclosed polygon ring should error",
    ),
    QueryTestCase(
        id="polygon_non_contained_hole",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]],
                            [[50, 50], [51, 50], [51, 51], [50, 51], [50, 50]],
                        ],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Polygon with non-contained hole should error",
    ),
    QueryTestCase(
        id="multipolygon_non_contained_hole",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]],
                                [[50, 50], [51, 50], [51, 51], [50, 51], [50, 50]],
                            ]
                        ],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="MultiPolygon with non-contained hole should error",
    ),
    QueryTestCase(
        id="missing_type_field",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {"coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geometry without type field should error",
    ),
    QueryTestCase(
        id="missing_coordinates_field",
        filter={"loc": {"$geoWithin": {"$geometry": {"type": "Polygon"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$geometry without coordinates field should error",
    ),
    QueryTestCase(
        id="non_string_type_field",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": 123,
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geometry with non-string type field should error",
    ),
    QueryTestCase(
        id="invalid_geometry_type_point",
        filter={"loc": {"$geoWithin": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Invalid geometry type Point should error",
    ),
    QueryTestCase(
        id="invalid_geometry_type_multipoint",
        filter={
            "loc": {
                "$geoWithin": {"$geometry": {"type": "MultiPoint", "coordinates": [[0, 0], [1, 1]]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid geometry type MultiPoint should error",
    ),
    QueryTestCase(
        id="invalid_geometry_type_multilinestring",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {"type": "MultiLineString", "coordinates": [[[0, 0], [1, 1]]]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Invalid geometry type MultiLineString should error",
    ),
    QueryTestCase(
        id="geometry_value_numeric",
        filter={"loc": {"$geoWithin": {"$geometry": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$geometry with numeric value should error",
    ),
    QueryTestCase(
        id="geometry_value_empty_string",
        filter={"loc": {"$geoWithin": {"$geometry": ""}}},
        error_code=BAD_VALUE_ERROR,
        msg="$geometry with empty string value should error",
    ),
    QueryTestCase(
        id="geometry_value_boolean",
        filter={"loc": {"$geoWithin": {"$geometry": False}}},
        error_code=BAD_VALUE_ERROR,
        msg="$geometry with boolean value should error",
    ),
    QueryTestCase(
        id="geometry_value_empty_array",
        filter={"loc": {"$geoWithin": {"$geometry": []}}},
        error_code=BAD_VALUE_ERROR,
        msg="$geometry with empty array value should error",
    ),
    QueryTestCase(
        id="geojson_without_geometry_wrapper",
        filter={
            "loc": {
                "$geoWithin": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeoJSON object directly in $geoWithin without $geometry wrapper should error",
    ),
]


CRS_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="invalid_crs_type",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        "crs": {
                            "type": "link",
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
                        },
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="crs.type other than 'name' should error",
    ),
    QueryTestCase(
        id="missing_crs_type",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        "crs": {
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"}
                        },
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="crs without type field should error",
    ),
    QueryTestCase(
        id="missing_crs_properties",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        "crs": {"type": "name"},
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="crs without properties field should error",
    ),
    QueryTestCase(
        id="unknown_crs_name",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        "crs": {"type": "name", "properties": {"name": "urn:bogus:not-a-real-crs"}},
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Unknown crs.properties.name URN should error",
    ),
    QueryTestCase(
        id="missing_crs_properties_name",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        "crs": {"type": "name", "properties": {}},
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="crs.properties without name field should error",
    ),
]


LEGACY_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="negative_radius",
        filter={"loc": {"$geoWithin": {"$centerSphere": [[0, 0], -1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$centerSphere negative radius should error",
    ),
    QueryTestCase(
        id="center_negative_radius",
        filter={"loc": {"$geoWithin": {"$center": [[0, 0], -1]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$center with negative radius should error",
    ),
    QueryTestCase(
        id="box_single_corner",
        filter={"loc": {"$geoWithin": {"$box": [[0, 0]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$box with only one corner should error",
    ),
    QueryTestCase(
        id="polygon_two_points",
        filter={"loc": {"$geoWithin": {"$polygon": [[0, 0], [10, 10]]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$polygon with fewer than 3 points should error",
    ),
    QueryTestCase(
        id="multiple_shape_specifiers",
        filter={
            "loc": {
                "$geoWithin": {
                    "$polygon": [[0, 0], [0, 10], [10, 10], [10, 0]],
                    "$box": [[0, 0], [10, 10]],
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Multiple shape specifiers in one $geoWithin should error",
    ),
]


ALL_ERROR_TESTS = GEOJSON_ERROR_TESTS + CRS_ERROR_TESTS + LEGACY_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_geoWithin_errors(collection, test):
    """Test $geoWithin rejects invalid arguments, coordinates, geometry, and shape parameters."""
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code)
