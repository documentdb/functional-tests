"""Tests for the $search geoWithin and geoShape operators."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    create_search_index,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework import fixtures
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    SEARCH_EXECUTOR_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import (
    Contains,
    Len,
)
from documentdb_tests.framework.test_constants import (
    DOUBLE_ZERO,
)

pytestmark = pytest.mark.requires(search=True)


_GEO_DOCS = [
    {
        "_id": 1,
        "loc": {"type": "Point", "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO]},
        "shaped": {"type": "Point", "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO]},
    },
    {
        "_id": 2,
        "loc": {"type": "Point", "coordinates": [1.0, 1.0]},
        "shaped": {"type": "Point", "coordinates": [1.0, 1.0]},
    },
    {
        "_id": 3,
        "loc": {"type": "Point", "coordinates": [5.0, 5.0]},
        "shaped": {"type": "Point", "coordinates": [5.0, 5.0]},
    },
    {
        "_id": 4,
        "loc": {"type": "Point", "coordinates": [10.0, 10.0]},
        "shaped": {"type": "Point", "coordinates": [10.0, 10.0]},
    },
    {
        "_id": 5,
        "loc": {"type": "Point", "coordinates": [-3.0, -3.0]},
        "shaped": {"type": "Point", "coordinates": [-3.0, -3.0]},
    },
]

_GEO_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "loc": {"type": "geo"},
            "shaped": {"type": "geo", "indexShapes": True},
        },
    }
}


@pytest.fixture(scope="module")
def geo_collection(engine_client, worker_id):
    """A module-scoped collection with a static search index mapping a geo-typed
    field, shared read-only across the geoWithin cases so the index is built and
    polled once."""
    db_name = fixtures.generate_database_name("stages_search_geo", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["geo"]
    coll.insert_many(_GEO_DOCS)
    create_search_index(coll, _GEO_INDEX_DEFINITION)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)


# Property [GeoWithin Region Matching]: geoWithin selects exactly the documents
# whose stored point lies inside the requested box or circle region.
SEARCH_GEO_WITHIN_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geo_within_box",
        pipeline=[
            {
                "$search": {
                    "geoWithin": {
                        "path": "loc",
                        "box": {
                            "bottomLeft": {"type": "Point", "coordinates": [-1.0, -1.0]},
                            "topRight": {"type": "Point", "coordinates": [6.0, 6.0]},
                        },
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 1),
                Contains("_id", 2),
                Contains("_id", 3),
            ]
        },
        msg="$search geoWithin should match the documents whose point lies inside the box region",
    ),
    StageTestCase(
        "geo_within_circle",
        pipeline=[
            {
                "$search": {
                    "geoWithin": {
                        "path": "loc",
                        "circle": {
                            "center": {
                                "type": "Point",
                                "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO],
                            },
                            "radius": 200_000,
                        },
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$search geoWithin should match the documents whose point lies inside the circle "
        "region",
    ),
    StageTestCase(
        "geo_within_geometry_polygon",
        pipeline=[
            {
                "$search": {
                    "geoWithin": {
                        "path": "loc",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-1.0, -1.0],
                                    [-1.0, 3.0],
                                    [3.0, 3.0],
                                    [3.0, -1.0],
                                    [-1.0, -1.0],
                                ]
                            ],
                        },
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$search geoWithin should match the documents whose point lies inside the geometry "
        "polygon region",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_GEO_WITHIN_TESTS))
def test_search_geo_within_cases(geo_collection, test_case: StageTestCase):
    """Test $search geoWithin box and circle region matching over a geo-mapped path."""
    result = execute_command(
        geo_collection,
        {"aggregate": geo_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [GeoShape Region Matching]: over a geo path indexed with
# indexShapes=true, geoShape selects exactly the documents whose stored point
# satisfies the requested relation to the geometry.
SEARCH_GEO_SHAPE_MATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geo_shape_within_polygon",
        pipeline=[
            {
                "$search": {
                    "geoShape": {
                        "path": "shaped",
                        "relation": "within",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-1.0, -1.0],
                                    [-1.0, 3.0],
                                    [3.0, 3.0],
                                    [3.0, -1.0],
                                    [-1.0, -1.0],
                                ]
                            ],
                        },
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$search geoShape within should match the points inside the polygon and exclude "
        "those outside it",
    ),
    StageTestCase(
        "geo_shape_intersects_polygon",
        pipeline=[
            {
                "$search": {
                    "geoShape": {
                        "path": "shaped",
                        "relation": "intersects",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-1.0, -1.0],
                                    [-1.0, 3.0],
                                    [3.0, 3.0],
                                    [3.0, -1.0],
                                    [-1.0, -1.0],
                                ]
                            ],
                        },
                    }
                }
            },
        ],
        expected={"cursor.firstBatch": [Len(2), Contains("_id", 1), Contains("_id", 2)]},
        msg="$search geoShape intersects should match the points that intersect the polygon",
    ),
    StageTestCase(
        "geo_shape_disjoint_polygon",
        pipeline=[
            {
                "$search": {
                    "geoShape": {
                        "path": "shaped",
                        "relation": "disjoint",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-1.0, -1.0],
                                    [-1.0, 3.0],
                                    [3.0, 3.0],
                                    [3.0, -1.0],
                                    [-1.0, -1.0],
                                ]
                            ],
                        },
                    }
                }
            },
        ],
        expected={
            "cursor.firstBatch": [
                Len(3),
                Contains("_id", 3),
                Contains("_id", 4),
                Contains("_id", 5),
            ]
        },
        msg="$search geoShape disjoint should match the points that do not intersect the polygon",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_GEO_SHAPE_MATCH_TESTS))
def test_search_geo_shape_cases(geo_collection, test_case: StageTestCase):
    """Test $search geoShape region matching over an indexShapes geo-mapped path."""
    result = execute_command(
        geo_collection,
        {"aggregate": geo_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        msg=test_case.msg,
        raw_res=True,
    )


# Property [GeoWithin Coordinate Validation]: geoWithin validates shape
# coordinates before the index check.
SEARCH_GEO_WITHIN_COORDINATE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geo_within_invalid_latitude",
        pipeline=[
            {
                "$search": {
                    "geoWithin": {
                        "path": "loc",
                        "box": {
                            "bottomLeft": {"type": "Point", "coordinates": [DOUBLE_ZERO, 91.0]},
                            "topRight": {"type": "Point", "coordinates": [6.0, 6.0]},
                        },
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoWithin should reject a latitude outside the valid range",
    ),
    StageTestCase(
        "geo_within_invalid_longitude",
        pipeline=[
            {
                "$search": {
                    "geoWithin": {
                        "path": "loc",
                        "box": {
                            "bottomLeft": {
                                "type": "Point",
                                "coordinates": [181.0, DOUBLE_ZERO],
                            },
                            "topRight": {"type": "Point", "coordinates": [6.0, 6.0]},
                        },
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoWithin should reject a longitude outside the valid range",
    ),
    StageTestCase(
        "geo_within_negative_radius",
        pipeline=[
            {
                "$search": {
                    "geoWithin": {
                        "path": "loc",
                        "circle": {
                            "center": {
                                "type": "Point",
                                "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO],
                            },
                            "radius": -1,
                        },
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoWithin should reject a negative circle radius",
    ),
    StageTestCase(
        "geo_within_coordinate_too_few_numbers",
        pipeline=[
            {
                "$search": {
                    "geoWithin": {
                        "path": "loc",
                        "box": {
                            "bottomLeft": {"type": "Point", "coordinates": [DOUBLE_ZERO]},
                            "topRight": {"type": "Point", "coordinates": [6.0, 6.0]},
                        },
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoWithin should reject a coordinate with fewer than two numbers",
    ),
]

# Property [GeoWithin Shape Required]: a geoWithin with no shape key produces an
# error.
SEARCH_GEO_WITHIN_SHAPE_REQUIRED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geo_within_no_shape",
        pipeline=[{"$search": {"geoWithin": {"path": "loc"}}}],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoWithin should reject a spec with no shape key",
    ),
]

SEARCH_GEO_WITHIN_ERROR_TESTS = (
    SEARCH_GEO_WITHIN_COORDINATE_ERROR_TESTS + SEARCH_GEO_WITHIN_SHAPE_REQUIRED_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_GEO_WITHIN_ERROR_TESTS))
def test_search_geo_within_errors(geo_collection, test_case: StageTestCase):
    """Test $search geoWithin rejects invalid coordinates and a missing shape key."""
    result = execute_command(
        geo_collection,
        {"aggregate": geo_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)


# Property [GeoShape Geometry Validation]: geoShape validates the relation enum
# and geometry shape before the index check.
SEARCH_GEO_SHAPE_GEOMETRY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geo_shape_invalid_relation",
        pipeline=[
            {
                "$search": {
                    "geoShape": {
                        "path": "loc",
                        "relation": "bogus",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [DOUBLE_ZERO, DOUBLE_ZERO],
                                    [DOUBLE_ZERO, 5.0],
                                    [5.0, 5.0],
                                    [5.0, DOUBLE_ZERO],
                                    [DOUBLE_ZERO, DOUBLE_ZERO],
                                ]
                            ],
                        },
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoShape should reject a relation outside the allowed set",
    ),
    StageTestCase(
        "geo_shape_polygon_too_few_positions",
        pipeline=[
            {
                "$search": {
                    "geoShape": {
                        "path": "loc",
                        "relation": "intersects",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [DOUBLE_ZERO, DOUBLE_ZERO],
                                    [DOUBLE_ZERO, 5.0],
                                    [DOUBLE_ZERO, DOUBLE_ZERO],
                                ]
                            ],
                        },
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoShape should reject a polygon with fewer than four positions",
    ),
    StageTestCase(
        "geo_shape_within_with_point",
        pipeline=[
            {
                "$search": {
                    "geoShape": {
                        "path": "loc",
                        "relation": "within",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [DOUBLE_ZERO, DOUBLE_ZERO],
                        },
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoShape should reject the within relation applied to a Point geometry",
    ),
]

# Property [GeoShape IndexShapes Requirement]: geoShape against a geo path not
# indexed with indexShapes=true produces an error.
SEARCH_GEO_SHAPE_INDEX_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geo_shape_path_not_index_shapes",
        pipeline=[
            {
                "$search": {
                    "geoShape": {
                        "path": "loc",
                        "relation": "intersects",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [DOUBLE_ZERO, DOUBLE_ZERO],
                                    [DOUBLE_ZERO, 5.0],
                                    [5.0, 5.0],
                                    [5.0, DOUBLE_ZERO],
                                    [DOUBLE_ZERO, DOUBLE_ZERO],
                                ]
                            ],
                        },
                    }
                }
            },
        ],
        error_code=SEARCH_EXECUTOR_ERROR,
        msg="$search geoShape should reject a geo path not indexed with indexShapes=true",
    ),
]

SEARCH_GEO_SHAPE_ERROR_TESTS = (
    SEARCH_GEO_SHAPE_GEOMETRY_ERROR_TESTS + SEARCH_GEO_SHAPE_INDEX_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCH_GEO_SHAPE_ERROR_TESTS))
def test_search_geo_shape_errors(geo_collection, test_case: StageTestCase):
    """Test $search geoShape rejects invalid geometry and a non-indexShapes geo path."""
    result = execute_command(
        geo_collection,
        {"aggregate": geo_collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
