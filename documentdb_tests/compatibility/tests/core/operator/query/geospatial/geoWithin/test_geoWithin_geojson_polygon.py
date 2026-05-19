"""
Tests for $geoWithin GeoJSON polygon edge cases, big polygons, and meridian-crossing polygons.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Big polygon covering most of the earth (> hemisphere)
BIG_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[-170, -80], [170, -80], [170, 80], [-170, 80], [-170, -80]]],
    "crs": {"type": "name", "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"}},
}

# Complementary polygon (small area NOT covered by big polygon)
SMALL_COMPLEMENT = {
    "type": "Polygon",
    "coordinates": [[[-170, 80], [170, 80], [170, -80], [-170, -80], [-170, 80]]],
    "crs": {"type": "name", "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"}},
}


POLYGON_EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="correct_lon_lat_order",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[39, 4], [41, 4], [41, 6], [39, 6], [39, 4]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [40, 5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [40, 5]}}],
        msg="Correct [longitude, latitude] order should return correct results",
    ),
    QueryTestCase(
        id="swapped_lon_lat_should_not_match",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[39, 4], [41, 4], [41, 6], [39, 6], [39, 4]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 40]}},
        ],
        expected=[],
        msg="Point with swapped [lat, lon] order should NOT match the polygon",
    ),
    QueryTestCase(
        id="point_at_null_island",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Point at [0, 0] (null island) should match",
    ),
    QueryTestCase(
        id="point_at_extreme_coords",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[179, 88], [180, 88], [180, 90], [179, 90], [179, 88]]],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 89]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 89]}}],
        msg="Point at extreme coordinates [180, 89] should match",
    ),
    QueryTestCase(
        id="very_small_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[0, 0], [0.0001, 0], [0.0001, 0.0001], [0, 0.0001], [0, 0]]
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.00001, 0.00001]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.00001, 0.00001]}}],
        msg="Very small polygon should match point inside",
    ),
    QueryTestCase(
        id="duplicate_consecutive_vertices",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-1, -1], [-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Polygon with duplicate consecutive vertices should still match",
    ),
    QueryTestCase(
        id="point_inside_close_to_boundary",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [9.999, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [9.999, 0]}}],
        msg="Point very close to boundary (inside) should match",
    ),
    QueryTestCase(
        id="point_outside_close_to_boundary",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [10.001, 0]}}],
        expected=[],
        msg="Point very close to boundary (outside) should not match",
    ),
    QueryTestCase(
        id="polygon_sharing_edge",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [15, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}}],
        msg="Only point inside polygon should match, not one sharing edge outside",
    ),
]


BIG_POLYGON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="big_polygon_with_strictwinding",
        filter={"loc": {"$geoWithin": {"$geometry": BIG_POLYGON}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-50, -50]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [175, 85]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [50, 50]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [-50, -50]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [175, 85]}},
        ],
        msg="Big polygon (>hemisphere) with strictwinding CRS should cover most of earth",
    ),
    QueryTestCase(
        id="reverse_winding_returns_complement",
        filter={"loc": {"$geoWithin": {"$geometry": SMALL_COMPLEMENT}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [175, 85]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [179, 0]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [-179, 0]}},
        ],
        expected=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [179, 0]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [-179, 0]}},
        ],
        msg="Reversed winding with strictwinding CRS returns complement (antimeridian sliver)",
    ),
]


MERIDIAN_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="polygon_crossing_antimeridian",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[178, -2], [-178, -2], [-178, 2], [178, 2], [178, -2]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [179.5, 0.5]}},
            {"_id": 4, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [179.5, 0.5]}},
        ],
        msg="Polygon crossing antimeridian should match points near dateline",
    ),
]


ALL_TESTS = POLYGON_EDGE_CASE_TESTS + BIG_POLYGON_TESTS + MERIDIAN_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geoWithin_polygon(collection, test):
    """Test $geoWithin polygon edge cases, big polygons, and meridian-crossing polygons."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
