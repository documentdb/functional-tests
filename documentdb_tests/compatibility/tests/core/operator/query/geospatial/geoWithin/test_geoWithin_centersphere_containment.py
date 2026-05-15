"""
Tests for $geoWithin $centerSphere containment of non-Point geometry types
(LineString, Polygon, MultiPolygon).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Spherical cap centered at [0, 0] with radius ~111km (0.01 radians ≈ 0.57 degrees)
SMALL_CAP = {"$centerSphere": [[0, 0], 0.01]}

# Larger cap centered at [0, 0] with radius ~1111km (0.1 radians ≈ 5.7 degrees)
LARGE_CAP = {"$centerSphere": [[0, 0], 0.1]}


CENTERSPHERE_LINESTRING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="linestring_entirely_within_cap",
        filter={"geo": {"$geoWithin": LARGE_CAP}},
        doc=[
            {"_id": 1, "geo": {"type": "LineString", "coordinates": [[0.1, 0.1], [0.2, 0.2]]}},
            {"_id": 2, "geo": {"type": "LineString", "coordinates": [[0, 0], [20, 20]]}},
        ],
        expected=[
            {"_id": 1, "geo": {"type": "LineString", "coordinates": [[0.1, 0.1], [0.2, 0.2]]}}
        ],
        msg="LineString entirely within $centerSphere should match",
    ),
    QueryTestCase(
        id="linestring_intersecting_cap_no_match",
        filter={"geo": {"$geoWithin": SMALL_CAP}},
        doc=[{"_id": 1, "geo": {"type": "LineString", "coordinates": [[0, 0], [5, 5]]}}],
        expected=[],
        msg="LineString intersecting but not entirely within $centerSphere should not match",
    ),
    QueryTestCase(
        id="linestring_outside_cap_no_match",
        filter={"geo": {"$geoWithin": SMALL_CAP}},
        doc=[{"_id": 1, "geo": {"type": "LineString", "coordinates": [[10, 10], [11, 11]]}}],
        expected=[],
        msg="LineString entirely outside $centerSphere should not match",
    ),
]


CENTERSPHERE_POLYGON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="polygon_entirely_within_cap",
        filter={"geo": {"$geoWithin": LARGE_CAP}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "Polygon",
                    "coordinates": [[[0.1, 0.1], [0.2, 0.1], [0.2, 0.2], [0.1, 0.2], [0.1, 0.1]]],
                },
            },
            {
                "_id": 2,
                "geo": {
                    "type": "Polygon",
                    "coordinates": [[[20, 20], [21, 20], [21, 21], [20, 21], [20, 20]]],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "geo": {
                    "type": "Polygon",
                    "coordinates": [[[0.1, 0.1], [0.2, 0.1], [0.2, 0.2], [0.1, 0.2], [0.1, 0.1]]],
                },
            }
        ],
        msg="Polygon entirely within $centerSphere should match",
    ),
    QueryTestCase(
        id="polygon_intersecting_cap_no_match",
        filter={"geo": {"$geoWithin": SMALL_CAP}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]]],
                },
            }
        ],
        expected=[],
        msg="Polygon intersecting but not entirely within $centerSphere should not match",
    ),
    QueryTestCase(
        id="polygon_outside_cap_no_match",
        filter={"geo": {"$geoWithin": SMALL_CAP}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "Polygon",
                    "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]],
                },
            }
        ],
        expected=[],
        msg="Polygon entirely outside $centerSphere should not match",
    ),
]


CENTERSPHERE_MULTIPOLYGON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="multipolygon_all_within_cap",
        filter={"geo": {"$geoWithin": LARGE_CAP}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[0.1, 0.1], [0.2, 0.1], [0.2, 0.2], [0.1, 0.2], [0.1, 0.1]]],
                        [[[0.3, 0.3], [0.4, 0.3], [0.4, 0.4], [0.3, 0.4], [0.3, 0.3]]],
                    ],
                },
            },
            {
                "_id": 2,
                "geo": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[0.1, 0.1], [0.2, 0.1], [0.2, 0.2], [0.1, 0.2], [0.1, 0.1]]],
                        [[[20, 20], [21, 20], [21, 21], [20, 21], [20, 20]]],
                    ],
                },
            },
        ],
        expected=[
            {
                "_id": 1,
                "geo": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[0.1, 0.1], [0.2, 0.1], [0.2, 0.2], [0.1, 0.2], [0.1, 0.1]]],
                        [[[0.3, 0.3], [0.4, 0.3], [0.4, 0.4], [0.3, 0.4], [0.3, 0.3]]],
                    ],
                },
            }
        ],
        msg="MultiPolygon with all polygons within $centerSphere should match",
    ),
    QueryTestCase(
        id="multipolygon_one_outside_no_match",
        filter={"geo": {"$geoWithin": SMALL_CAP}},
        doc=[
            {
                "_id": 1,
                "geo": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [0.001, 0.001],
                                [0.002, 0.001],
                                [0.002, 0.002],
                                [0.001, 0.002],
                                [0.001, 0.001],
                            ]
                        ],
                        [[[20, 20], [21, 20], [21, 21], [20, 21], [20, 20]]],
                    ],
                },
            }
        ],
        expected=[],
        msg="MultiPolygon with one polygon outside $centerSphere should not match",
    ),
]


ALL_TESTS = (
    CENTERSPHERE_LINESTRING_TESTS + CENTERSPHERE_POLYGON_TESTS + CENTERSPHERE_MULTIPOLYGON_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geoWithin_centersphere_containment(collection, test):
    """Test $geoWithin $centerSphere containment of non-Point geometry types."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
