"""Tests for $geometry polygon edge cases — odd shapes, hemisphere auto-correction,
mixed GeoJSON/legacy documents, polygon holes, null/missing field handling,
and winding order with CRS."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

STRICT_CRS = {
    "type": "name",
    "properties": {"name": "urn:x-mongodb:crs:strictwinding:EPSG:4326"},
}

ODD_SHAPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="tall_narrow_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-0.5, -89], [0.5, -89], [0.5, 89], [-0.5, 89], [-0.5, -89]]
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should find point inside tall narrow polygon (1 degree wide, 178 degrees tall)",
    ),
    QueryTestCase(
        id="very_small_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [0.001, 0], [0.001, 0.001], [0, 0.001], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.0005, 0.0005]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.0005, 0.0005]}}],
        msg="Should find point inside very small polygon",
    ),
    QueryTestCase(
        id="antimeridian_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[179, -1], [-179, -1], [-179, 1], [179, 1], [179, -1]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [179.5, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [179.5, 0]}}],
        msg="Should find point inside polygon spanning antimeridian",
    ),
    QueryTestCase(
        id="pole_containing_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-180, 80], [0, 80], [180, 80], [-180, 80]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 89]}}],
        msg="Should find point inside polygon containing the North Pole",
    ),
    QueryTestCase(
        id="many_vertices_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[i * 0.36 - 180, -0.5 if i % 2 == 0 else 0.5] for i in range(1000)]
                            + [[-180, -0.5]]
                        ],
                    }
                }
            }
        },
        doc=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should accept polygon with 1000+ vertices",
    ),
    QueryTestCase(
        id="collinear_points_polygon",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [2, 0], [2, 1], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0.5]}}],
        msg="Should accept polygon with collinear points on edge",
    ),
    QueryTestCase(
        id="duplicate_consecutive_vertices",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [5, 5]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="Should accept polygon with duplicate consecutive vertices",
    ),
    QueryTestCase(
        id="degenerate_same_location_points",
        filter={
            "loc": {
                "$geoIntersects": {
                    "$geometry": {"type": "MultiPoint", "coordinates": [[0, 0], [0, 0], [0, 0]]}
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 1]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should handle degenerate geometry (all points same location)",
    ),
    QueryTestCase(
        id="large_polygon_greater_than_hemisphere",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[-170, -80], [170, -80], [170, 80], [-170, 80], [-170, -80]]
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [170, 80]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [170, 80]}}],
        msg="Polygon larger than hemisphere should be auto-corrected to smaller complement area",
    ),
    QueryTestCase(
        id="mixed_geojson_and_legacy_docs",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-1, -1], [2, -1], [2, 2], [-1, 2], [-1, -1]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": [1, 1]},
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": [1, 1]},
        ],
        msg="Should match both GeoJSON and legacy coordinate pair documents",
    ),
]


POLYGON_HOLE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="polygon_with_hole",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]],
                            [
                                [0.1, 0.1],
                                [0.1, 0.9],
                                [0.9, 0.9],
                                [0.9, 0.1],
                                [0.1, 0.1],
                            ],
                        ],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [3, 3]}},
            {"_id": 3, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [3, 3]}}],
        msg="Should exclude points inside the hole",
    ),
]


NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_location_not_matched",
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
        doc=[
            {"_id": 1, "loc": None},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should not match documents where location field is null",
    ),
    QueryTestCase(
        id="missing_location_not_matched",
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
        doc=[
            {"_id": 1, "name": "no_loc"},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [0, 0]}}],
        msg="Should not match documents where location field is missing",
    ),
]


WINDING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="cw_winding_matches_interior",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[{"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}}],
        msg="CW polygon without strict CRS auto-corrects to smaller area (interior)",
    ),
    QueryTestCase(
        id="strict_crs_cw_matches_complement",
        filter={
            "loc": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
                        "crs": STRICT_CRS,
                    }
                }
            }
        },
        doc=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0.5, 0.5]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}},
        ],
        expected=[{"_id": 2, "loc": {"type": "Point", "coordinates": [10, 10]}}],
        msg="CW polygon with strict winding CRS should still match complement",
    ),
]


ALL_TESTS = ODD_SHAPE_TESTS + POLYGON_HOLE_TESTS + NULL_MISSING_TESTS + WINDING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_geometry_polygon_edge_cases(collection, test):
    """Verifies $geometry handles polygon edge cases correctly."""
    collection.create_index([("loc", "2dsphere")])
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
