"""
Tests for $geoIntersects error cases — invalid arguments, invalid geometry,
coordinate validation, legacy coordinate doc form validation, polygon validation,
syntax errors, operator combination errors, NaN/Infinity, CRS type restrictions,
and extra operator errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Standard query polygon for reuse
QUERY_POLYGON = {
    "$geometry": {
        "type": "Polygon",
        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
    }
}


INVALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="no_geometry_operator",
        filter={"loc": {"$geoIntersects": {}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty $geoIntersects object without $geometry should error",
    ),
    QueryTestCase(
        id="null_value",
        filter={"loc": {"$geoIntersects": None}},
        error_code=BAD_VALUE_ERROR,
        msg="Null $geoIntersects value should error",
    ),
    QueryTestCase(
        id="numeric_value",
        filter={"loc": {"$geoIntersects": 123}},
        error_code=BAD_VALUE_ERROR,
        msg="Numeric $geoIntersects value should error",
    ),
    QueryTestCase(
        id="string_value",
        filter={"loc": {"$geoIntersects": "invalid"}},
        error_code=BAD_VALUE_ERROR,
        msg="String $geoIntersects value should error",
    ),
    QueryTestCase(
        id="array_value",
        filter={"loc": {"$geoIntersects": [1, 2]}},
        error_code=BAD_VALUE_ERROR,
        msg="Array $geoIntersects value should error",
    ),
    QueryTestCase(
        id="boolean_value",
        filter={"loc": {"$geoIntersects": True}},
        error_code=BAD_VALUE_ERROR,
        msg="Boolean $geoIntersects value should error",
    ),
    QueryTestCase(
        id="top_level_geoIntersects_rejected",
        filter={"$geoIntersects": QUERY_POLYGON},
        error_code=BAD_VALUE_ERROR,
        msg="$geoIntersects as top-level filter should error",
    ),
]


INVALID_GEOMETRY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geometry_empty_object",
        filter={"loc": {"$geoIntersects": {"$geometry": {}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty $geometry object should error",
    ),
    QueryTestCase(
        id="geometry_missing_type",
        filter={"loc": {"$geoIntersects": {"$geometry": {"coordinates": [[0, 0], [1, 1]]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$geometry missing type field should error",
    ),
    QueryTestCase(
        id="geometry_missing_coordinates",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$geometry missing coordinates field should error",
    ),
    QueryTestCase(
        id="geometry_unknown_type",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Unknown", "coordinates": [[0, 0], [1, 1]]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geometry with unknown type should error",
    ),
    QueryTestCase(
        id="geometry_type_feature",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Feature", "coordinates": [[0, 0], [1, 1]]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geometry type Feature should error",
    ),
    QueryTestCase(
        id="legacy_doc_three_fields_with_non_numeric",
        filter={"loc": {"$geoIntersects": {"$geometry": {"z": "str", "x": 0, "y": 0}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Legacy doc form with 3 fields including non-numeric in first position should error",
    ),
    QueryTestCase(
        id="legacy_doc_three_fields_non_numeric_last",
        filter={"loc": {"$geoIntersects": {"$geometry": {"x": 0, "y": 0, "z": "str"}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Legacy doc form with 3 fields including non-numeric in last position should error",
    ),
    QueryTestCase(
        id="legacy_doc_three_fields_all_numeric",
        filter={"loc": {"$geoIntersects": {"$geometry": {"x": 0, "y": 0, "z": 99}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Legacy doc form with 3 numeric fields should error",
    ),
    QueryTestCase(
        id="legacy_doc_single_field",
        filter={"loc": {"$geoIntersects": {"$geometry": {"x": 0}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Legacy doc form with single field should error",
    ),
]


INVALID_COORDINATES_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="coordinates_empty_array_point",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": []}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Empty coordinates array for Point should error",
    ),
    QueryTestCase(
        id="coordinates_single_value_point",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0]}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Single coordinate for Point should error",
    ),
    QueryTestCase(
        id="coordinates_non_numeric_values",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": ["a", "b"]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Non-numeric coordinate values should error",
    ),
    QueryTestCase(
        id="coordinates_object_non_numeric_in_pos1",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": {"z": "str", "x": 0, "y": 0},
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Coordinates object with non-numeric in position 1 should error",
    ),
    QueryTestCase(
        id="coordinates_object_non_numeric_first_of_three",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": {"a": "str", "b": 0, "c": 0},
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Coordinates object with non-numeric in first position should error",
    ),
    QueryTestCase(
        id="coordinates_object_single_field",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": {"x": 0}}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Coordinates object with single field should error",
    ),
]


INVALID_GEOMETRY_COLLECTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geometrycollection_geometries_null",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "GeometryCollection", "geometries": None}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeometryCollection with null geometries should error",
    ),
    QueryTestCase(
        id="geometrycollection_geometries_string",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "GeometryCollection", "geometries": "invalid"}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeometryCollection with string geometries should error",
    ),
    QueryTestCase(
        id="geometrycollection_geometries_number",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "GeometryCollection", "geometries": 123}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeometryCollection with numeric geometries should error",
    ),
    QueryTestCase(
        id="geometrycollection_geometries_boolean",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "GeometryCollection", "geometries": True}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeometryCollection with boolean geometries should error",
    ),
    QueryTestCase(
        id="geometrycollection_geometries_object",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "GeometryCollection",
                        "geometries": {"type": "Point", "coordinates": [0, 0]},
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeometryCollection with object geometries (not array) should error",
    ),
    QueryTestCase(
        id="geometrycollection_geometries_empty_array",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "GeometryCollection", "geometries": []}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeometryCollection with empty geometries array should error",
    ),
    QueryTestCase(
        id="geometrycollection_invalid_sub_geometry",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "GeometryCollection",
                        "geometries": [
                            {"type": "Point", "coordinates": [999, 999]},
                        ],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeometryCollection with invalid sub-geometry coordinates should error",
    ),
]


COORDINATE_VALIDATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_less_than_neg180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [-181, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Longitude < -180 should error",
    ),
    QueryTestCase(
        id="longitude_greater_than_180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [181, 0]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Longitude > 180 should error",
    ),
    QueryTestCase(
        id="latitude_less_than_neg90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, -91]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Latitude < -90 should error",
    ),
    QueryTestCase(
        id="latitude_greater_than_90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 91]}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Latitude > 90 should error",
    ),
    QueryTestCase(
        id="longitude_500_linestring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[500, 0], [1, 1]]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Longitude 500 in LineString should error",
    ),
    QueryTestCase(
        id="latitude_500_linestring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordinates": [[0, 500], [1, 1]]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Latitude 500 in LineString should error",
    ),
]


POLYGON_VALIDATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="unclosed_polygon",
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
        msg="Unclosed polygon should error",
    ),
    QueryTestCase(
        id="polygon_fewer_than_4_points",
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
        msg="Polygon with fewer than 4 points should error",
    ),
    QueryTestCase(
        id="self_intersecting_polygon",
        filter={
            "loc": {
                "$geoIntersects": {
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
        id="polygon_latitude_out_of_range",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 91], [1, 91], [1, 92], [0, 92], [0, 91]]],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Polygon with latitude > 90 should error",
    ),
    QueryTestCase(
        id="polygon_hole_outside_outer_ring",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]],
                            [[20, 20], [30, 20], [30, 30], [20, 30], [20, 20]],
                        ],
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Polygon with hole outside outer ring should error",
    ),
]


SYNTAX_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geojson_without_geometry_wrapper",
        filter={
            "loc": {
                "$geoIntersects": {
                    "type": "Point",
                    "coordinates": [0, 0],
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="GeoJSON without $geometry wrapper should error",
    ),
    QueryTestCase(
        id="misspelled_geometry_key",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geomtry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Misspelled $geometry key should error",
    ),
    QueryTestCase(
        id="misspelled_coordinates_key",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "LineString", "coordnates": [[0, 0], [1, 1]]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Misspelled coordinates key should error",
    ),
    QueryTestCase(
        id="linestring_empty_coordinates",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "LineString", "coordinates": []}}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="LineString with empty coordinates should error",
    ),
    QueryTestCase(
        id="linestring_single_point",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "LineString", "coordinates": [[0, 0]]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="LineString with single point should error",
    ),
    QueryTestCase(
        id="point_empty_coordinates",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": []}}}},
        error_code=BAD_VALUE_ERROR,
        msg="Point with empty coordinates should error",
    ),
]


OPERATOR_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="combined_with_near",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
                "$near": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geoIntersects combined with $near should error",
    ),
    QueryTestCase(
        id="combined_with_nearSphere",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
                "$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geoIntersects combined with $nearSphere should error",
    ),
    QueryTestCase(
        id="extra_geoNear_operator",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
                "$geoNear": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geoIntersects with extra $geoNear operator should error",
    ),
    QueryTestCase(
        id="combined_with_geoWithin",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                    }
                },
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geoIntersects combined with $geoWithin should error",
    ),
]


NAN_INF_COORDINATE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nan_longitude",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [FLOAT_NAN, 0]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="NaN longitude should error",
    ),
    QueryTestCase(
        id="nan_latitude",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, FLOAT_NAN]}}
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="NaN latitude should error",
    ),
    QueryTestCase(
        id="inf_longitude",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [FLOAT_INFINITY, 0]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Infinity longitude should error",
    ),
    QueryTestCase(
        id="inf_latitude",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [0, FLOAT_INFINITY]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Infinity latitude should error",
    ),
    QueryTestCase(
        id="neg_inf_longitude",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [FLOAT_NEGATIVE_INFINITY, 0]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative infinity longitude should error",
    ),
    QueryTestCase(
        id="neg_inf_latitude",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "Point", "coordinates": [0, FLOAT_NEGATIVE_INFINITY]}
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative infinity latitude should error",
    ),
]


CRS_TYPE_RESTRICTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="crs_on_point_type",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [0, 0],
                        "crs": {
                            "type": "name",
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
                        },
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Custom CRS on Point type should error (only Polygon supported)",
    ),
    QueryTestCase(
        id="crs_on_linestring_type",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "LineString",
                        "coordinates": [[0, 0], [1, 1]],
                        "crs": {
                            "type": "name",
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
                        },
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Custom CRS on LineString type should error (only Polygon supported)",
    ),
    QueryTestCase(
        id="crs_on_multipoint_type",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "MultiPoint",
                        "coordinates": [[0, 0], [1, 1]],
                        "crs": {
                            "type": "name",
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
                        },
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Custom CRS on MultiPoint type should error (only Polygon supported)",
    ),
    QueryTestCase(
        id="crs_on_multilinestring_type",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "MultiLineString",
                        "coordinates": [[[0, 0], [1, 1]], [[2, 2], [3, 3]]],
                        "crs": {
                            "type": "name",
                            "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
                        },
                    }
                }
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="Custom CRS on MultiLineString type should error (only Polygon supported)",
    ),
]


EXTRA_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="geoIntersects_with_eq_on_same_field",
        filter={
            "loc": {
                "$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 0]}},
                "$eq": {"type": "Point", "coordinates": [0, 0]},
            }
        },
        error_code=BAD_VALUE_ERROR,
        msg="$geoIntersects with $eq on same field should error",
    ),
]

ALL_ERROR_TESTS = (
    INVALID_ARGUMENT_TESTS
    + INVALID_GEOMETRY_TESTS
    + INVALID_COORDINATES_TESTS
    + INVALID_GEOMETRY_COLLECTION_TESTS
    + COORDINATE_VALIDATION_TESTS
    + POLYGON_VALIDATION_TESTS
    + SYNTAX_ERROR_TESTS
    + OPERATOR_COMBINATION_TESTS
    + NAN_INF_COORDINATE_TESTS
    + CRS_TYPE_RESTRICTION_TESTS
    + EXTRA_OPERATOR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_geoIntersects_errors(collection, test):
    """Test $geoIntersects error cases."""
    collection.insert_one({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}})
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)
