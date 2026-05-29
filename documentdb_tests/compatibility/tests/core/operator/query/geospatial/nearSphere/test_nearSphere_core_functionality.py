"""Tests for $nearSphere core — nearest-first sorting, sort override, coordinate boundaries."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_NEGATIVE_ZERO

# Order matters — $nearSphere sorts by distance. Do NOT use ignore_doc_order=True.
SORT_AND_DISTANCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="default_sort_nearest_first",
        filter={"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}},
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}, "name": "far"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "origin"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 1]}, "name": "near"},
        ],
        expected=[
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "origin"},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [1, 1]}, "name": "near"},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [5, 5]}, "name": "far"},
        ],
        msg="Should sort by distance nearest first",
    ),
    QueryTestCase(
        id="legacy_spherical_distance_radians",
        filter={"loc": {"$nearSphere": [0, 0], "$maxDistance": 0.02}},
        doc=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
            {"_id": 3, "loc": [5, 0]},
        ],
        expected=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
        ],
        msg="Should use spherical distance in radians for legacy mode",
    ),
    QueryTestCase(
        id="legacy_distance_ordering",
        filter={"loc": {"$nearSphere": [0, 0]}},
        doc=[
            {"_id": 1, "loc": [5, 5]},
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [1, 1]},
        ],
        expected=[
            {"_id": 2, "loc": [0, 0]},
            {"_id": 3, "loc": [1, 1]},
            {"_id": 1, "loc": [5, 5]},
        ],
        msg="Should sort by spherical distance with legacy coordinates",
    ),
]


COORDINATE_BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="longitude_neg180",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [-180, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [-180, 0]}}],
        msg="Should accept longitude = -180",
    ),
    QueryTestCase(
        id="longitude_180",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [180, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}}],
        msg="Should accept longitude = 180",
    ),
    QueryTestCase(
        id="latitude_neg90",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, -90]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}}],
        msg="Should accept latitude = -90",
    ),
    QueryTestCase(
        id="latitude_90",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, 90]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}}],
        msg="Should accept latitude = 90",
    ),
    QueryTestCase(
        id="origin_null_island",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept origin [0, 0]",
    ),
    QueryTestCase(
        id="negative_zero_coordinate",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [DOUBLE_NEGATIVE_ZERO, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept negative zero coordinate",
    ),
    QueryTestCase(
        id="north_pole",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, 90]},
                    "$maxDistance": 20100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should query from North Pole",
    ),
    QueryTestCase(
        id="south_pole",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, -90]},
                    "$maxDistance": 20100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, -90]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        msg="Should query from South Pole",
    ),
    QueryTestCase(
        id="antimeridian_180",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [180, 0]},
                    "$maxDistance": 100000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-180, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [180, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-180, 0]}},
        ],
        msg="Should find points at antimeridian (180 and -180 are same location)",
    ),
    QueryTestCase(
        id="three_coordinates_altitude",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [-73.9667, 40.78, 0],
                    },
                    "$maxDistance": 50000000,
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept three-coordinate (altitude) GeoJSON point",
    ),
    QueryTestCase(
        id="distance_near_poles",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [0, 89]},
                    "$maxDistance": 250000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 89]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [180, 89]}},
        ],
        msg="Should find nearby point at poles where meridians converge",
    ),
    QueryTestCase(
        id="cross_antimeridian_query",
        filter={
            "loc": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": [179, 0]},
                    "$maxDistance": 300000,
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179, 0]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [-179, 0]}},
        ],
        msg="Should find points across antimeridian",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SORT_AND_DISTANCE_TESTS + COORDINATE_BOUNDARY_TESTS))
def test_nearSphere_core(collection, test):
    """Verifies $nearSphere core functionality."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)


def test_nearSphere_explicit_sort_overrides_distance(collection):
    """Verifies explicit sort overrides $nearSphere distance ordering."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(
        [
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "rank": 3},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "rank": 1},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "rank": 2},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}
            },
            "sort": {"rank": 1},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}, "rank": 1},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [2, 0]}, "rank": 2},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "rank": 3},
        ],
        msg="Should sort by explicit field, overriding distance",
    )
