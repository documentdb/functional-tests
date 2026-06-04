"""
Tests for $geoIntersects edge cases — boundary coordinates, precision,
complex geometries, spherical geometry, and big polygon/CRS behavior.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import CANT_EXTRACT_GEO_KEYS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_exactly_neg180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [-180, 0]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        msg="Longitude exactly -180 should be valid",
    ),
    QueryTestCase(
        id="longitude_exactly_180",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [180, 0]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        msg="Longitude exactly 180 should be valid",
    ),
    QueryTestCase(
        id="latitude_exactly_neg90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, -90]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        msg="Latitude exactly -90 should be valid",
    ),
    QueryTestCase(
        id="latitude_exactly_90",
        filter={
            "loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [0, 90]}}}
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        msg="Latitude exactly 90 should be valid",
    ),
    QueryTestCase(
        id="high_precision_coordinates",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [1.123456789012345, 2.987654321098765],
                    }
                }
            }
        },
        doc=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1.123456789012345, 2.987654321098765]},
            },
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1.123456789012345, 2.987654321098765]},
            }
        ],
        msg="High precision coordinates should be valid",
    ),
    QueryTestCase(
        id="integer_coordinates",
        filter={"loc": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": [5, 5]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}}],
        msg="Integer coordinates should be valid",
    ),
    QueryTestCase(
        id="polygon_with_hole",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]],
                            [[-2, -2], [2, -2], [2, 2], [-2, 2], [-2, -2]],
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}}],
        msg="Polygon with hole should not intersect points in the hole",
    ),
    QueryTestCase(
        id="polygon_many_vertices",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-5, -5],
                                [-4, -5],
                                [-3, -5],
                                [-2, -5],
                                [-1, -5],
                                [0, -5],
                                [1, -5],
                                [2, -5],
                                [3, -5],
                                [4, -5],
                                [5, -5],
                                [5, 5],
                                [-5, 5],
                                [-5, -5],
                            ]
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Polygon with many vertices should be valid",
    ),
    QueryTestCase(
        id="linestring_many_segments",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "LineString",
                        "coordinates": [[-5, 0], [-3, 0], [-1, 0], [1, 0], [3, 0], [5, 0]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="LineString with many segments should be valid",
    ),
    QueryTestCase(
        id="linestring_duplicate_points_valid",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "LineString",
                        "coordinates": [[0, 0], [0, 0], [1, 1]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="LineString with duplicate points should be valid",
    ),
    QueryTestCase(
        id="near_pole",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, 89], [10, 89], [10, 90], [-10, 90], [-10, 89]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89.5]}}],
        msg="Polygon near pole should intersect point at high latitude",
    ),
    QueryTestCase(
        id="antimeridian",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[179, -1], [-179, -1], [-179, 1], [179, 1], [179, -1]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179.5, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179.5, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179.5, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179.5, 0]}},
        ],
        msg="Polygon crossing antimeridian should intersect points on both sides",
    ),
    QueryTestCase(
        id="decimal128_coordinates",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                    }
                }
            }
        },
        doc=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [Decimal128("1.5"), Decimal128("1.5")]},
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [Decimal128("50.0"), Decimal128("50.0")]},
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [Decimal128("1.5"), Decimal128("1.5")]},
            },
        ],
        msg="Decimal128 coordinates should be supported",
    ),
    QueryTestCase(
        id="legacy_point_format",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": [1, 1]},
            {"_id": 2, "loc": [50, 50]},
        ],
        expected=[{"_id": 1, "loc": [1, 1]}],
        msg="Legacy coordinate pair format should be queryable with $geoIntersects",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_geoIntersects_edge_cases(collection, test):
    """Test $geoIntersects edge cases."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


STRICT_WINDING_CRS = {
    "type": "name",
    "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
}

BIG_POLYGON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="small_polygon_default_crs",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        msg="Small polygon with default CRS should return intersecting documents",
    ),
    QueryTestCase(
        id="custom_crs_counter_clockwise",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                        "crs": STRICT_WINDING_CRS,
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Custom CRS with CCW winding should match points inside small polygon",
    ),
    QueryTestCase(
        id="custom_crs_clockwise",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [-10, 10], [10, 10], [10, -10], [-10, -10]]],
                        "crs": STRICT_WINDING_CRS,
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}}],
        msg="Custom CRS with clockwise winding should match complement",
    ),
    QueryTestCase(
        id="complementary_big_polygon_no_crs",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [-10, 10], [10, 10], [10, -10], [-10, -10]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Clockwise polygon without CRS should be auto-corrected to small polygon",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BIG_POLYGON_TESTS))
def test_geoIntersects_big_polygon(collection, test):
    """Test $geoIntersects big polygon / CRS handling."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True, msg=test.msg)


def test_geoIntersects_big_polygon_index_restriction(collection):
    """Test that creating a 2dsphere index on big polygon document fails."""
    collection.insert_one(
        {
            "_id": 1,
            "loc": {
                "type": "Polygon",
                "coordinates": [[[-10, -10], [-10, 10], [10, 10], [10, -10], [-10, -10]]],
                "crs": STRICT_WINDING_CRS,
            },
        }
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2dsphere"}],
        },
    )
    assertFailureCode(
        result,
        CANT_EXTRACT_GEO_KEYS_ERROR,
        msg="Creating 2dsphere index on big polygon should fail",
    )
