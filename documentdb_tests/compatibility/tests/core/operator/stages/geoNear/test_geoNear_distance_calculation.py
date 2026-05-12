"""Tests for $geoNear distance calculation behavior."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, ObjectId, Regex, Timestamp
from bson.decimal128 import Decimal128
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_NAN,
    INT64_ZERO,
)

# Property [Nearest-First Ordering]: $geoNear returns results ordered from
# nearest to farthest relative to the query point.
GEONEAR_ORDERING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "ordering_geojson_points",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 3, "loc": {"type": "Point", "coordinates": [3, 0]}},
            {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [2, 0]},
                "dist": 222_637.69004290068,
            },
            {
                "_id": 3,
                "loc": {"type": "Point", "coordinates": [3, 0]},
                "dist": 333_956.53506435105,
            },
        ],
        msg="$geoNear should return results ordered nearest to farthest",
    ),
    StageTestCase(
        "ordering_legacy_2d",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[
            {"_id": 3, "loc": [3, 0]},
            {"_id": 1, "loc": [1, 0]},
            {"_id": 2, "loc": [2, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [0, 0], "distanceField": "dist", "spherical": False}}],
        expected=[
            {"_id": 1, "loc": [1, 0], "dist": 1.0},
            {"_id": 2, "loc": [2, 0], "dist": 2.0},
            {"_id": 3, "loc": [3, 0], "dist": 3.0},
        ],
        msg="$geoNear with 2d index should return results ordered nearest to farthest",
    ),
]

# Property [GeoJSON Distances in Meters]: when the near point is a GeoJSON
# object, distances are reported in meters.
GEONEAR_GEOJSON_METERS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geojson_distance_meters",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                # ~111.3 km: one degree of longitude at the equator on a WGS84 sphere
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear with GeoJSON near point should produce distances in meters",
    ),
]

# Property [Legacy Spherical Distances in Radians]: legacy coordinate pairs
# with spherical=true produce distances in radians.
GEONEAR_LEGACY_RADIANS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "legacy_spherical_radians",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [1, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [0, 0], "distanceField": "dist", "spherical": True}}],
        expected=[
            {"_id": 1, "loc": [0, 0], "dist": DOUBLE_ZERO},
            {"_id": 2, "loc": [1, 0], "dist": math.radians(1)},
        ],
        msg=(
            "$geoNear with legacy coordinates and spherical=true"
            " should produce distances in radians"
        ),
    ),
]

# Property [Legacy Planar Distances]: legacy coordinate pairs with a 2d index
# and spherical=false produce planar Euclidean distances.
GEONEAR_LEGACY_PLANAR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "legacy_2d_planar",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [3, 0]},
            {"_id": 3, "loc": [3, 4]},
        ],
        pipeline=[{"$geoNear": {"near": [0, 0], "distanceField": "dist", "spherical": False}}],
        expected=[
            {"_id": 1, "loc": [0, 0], "dist": DOUBLE_ZERO},
            {"_id": 2, "loc": [3, 0], "dist": 3.0},
            {"_id": 3, "loc": [3, 4], "dist": 5.0},
        ],
        msg=(
            "$geoNear with legacy coordinates and 2d index"
            " should produce planar Euclidean distances"
        ),
    ),
]

# Property [Perimeter Distance for Non-Point Shapes]: distance to polygon and
# line geometries is measured to the nearest perimeter point, with zero
# distance for points inside a polygon or on a line.
GEONEAR_PERIMETER_DISTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "polygon_inside_zero_distance",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]],
                },
            },
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [10.5, 10.5]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {
                    "type": "Polygon",
                    "coordinates": [[[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]],
                },
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear should report zero distance for a point inside a polygon",
    ),
    StageTestCase(
        "line_on_line_zero_distance",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {
                "_id": 1,
                "loc": {"type": "LineString", "coordinates": [[0, 0], [2, 0]]},
            },
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [1, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "LineString", "coordinates": [[0, 0], [2, 0]]},
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear should report zero distance for a point on a line",
    ),
    StageTestCase(
        "line_perpendicular_distance",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {
                "_id": 1,
                "loc": {"type": "LineString", "coordinates": [[0, 0], [2, 0]]},
            },
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [1, 1]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "LineString", "coordinates": [[0, 0], [2, 0]]},
                "dist": 111_318.84502145031,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145031,
            },
        ],
        msg="$geoNear should compute distance to the nearest perimeter point of a line",
    ),
]

# Property [Spherical Coercion]: the spherical parameter is coerced to
# boolean - falsy values select the 2d index for planar distances, truthy
# values select the 2dsphere index for spherical distances, and omission
# defaults to false.
GEONEAR_SPHERICAL_COERCION_TESTS: list[StageTestCase] = (
    [
        StageTestCase(
            f"spherical_{name}",
            indexes=[IndexModel([("loc", "2d")]), IndexModel([("loc", "2dsphere")])],
            docs=[
                {"_id": 1, "loc": [0, 0]},
                {"_id": 2, "loc": [3, 0]},
            ],
            pipeline=[
                {
                    "$geoNear": {
                        "near": [0, 0],
                        "distanceField": "dist",
                        "spherical": value,
                    }
                }
            ],
            expected=[
                {"_id": 1, "loc": [0, 0], "dist": DOUBLE_ZERO},
                {"_id": 2, "loc": [3, 0], "dist": 3.0},
            ],
            msg=f"$geoNear with spherical={value!r} should be treated as falsy",
        )
        for name, value in [
            ("false", False),
            ("null", None),
            ("int_zero", 0),
            ("long_zero", INT64_ZERO),
            ("double_zero", DOUBLE_ZERO),
            ("double_negative_zero", DOUBLE_NEGATIVE_ZERO),
            ("decimal128_zero", DECIMAL128_ZERO),
            ("decimal128_negative_zero", DECIMAL128_NEGATIVE_ZERO),
        ]
    ]
    + [
        StageTestCase(
            f"spherical_{name}",
            indexes=[IndexModel([("loc", "2d")]), IndexModel([("loc", "2dsphere")])],
            docs=[
                {"_id": 1, "loc": [0, 0]},
                {"_id": 2, "loc": [3, 0]},
            ],
            pipeline=[
                {
                    "$geoNear": {
                        "near": [0, 0],
                        "distanceField": "dist",
                        "spherical": value,
                    }
                }
            ],
            expected=[
                {"_id": 1, "loc": [0, 0], "dist": DOUBLE_ZERO},
                {"_id": 2, "loc": [3, 0], "dist": 0.0523598775598299},
            ],
            msg=f"$geoNear with spherical={value!r} should be treated as truthy",
        )
        for name, value in [
            ("true", True),
            ("nonzero_int", 42),
            ("nonzero_int64", Int64(1)),
            ("nonzero_double", 1.5),
            ("nonzero_decimal128", Decimal128("1")),
            ("nan", FLOAT_NAN),
            ("empty_string", ""),
            ("nonempty_string", "hello"),
            ("empty_array", []),
            ("nonempty_array", [1, 2]),
            ("empty_document", {}),
            ("nonempty_document", {"a": 1}),
            ("objectid", ObjectId("000000000000000000000001")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01")),
            ("regex", Regex("^a")),
        ]
    ]
    + [
        StageTestCase(
            "spherical_omitted_defaults_false",
            indexes=[IndexModel([("loc", "2d")]), IndexModel([("loc", "2dsphere")])],
            docs=[
                {"_id": 1, "loc": [0, 0]},
                {"_id": 2, "loc": [3, 0]},
            ],
            pipeline=[
                {
                    "$geoNear": {
                        "near": [0, 0],
                        "distanceField": "dist",
                    }
                }
            ],
            expected=[
                {"_id": 1, "loc": [0, 0], "dist": DOUBLE_ZERO},
                {"_id": 2, "loc": [3, 0], "dist": 3.0},
            ],
            msg="$geoNear with spherical omitted should default to false (planar distances)",
        ),
    ]
)

# Property [Decimal128 Underflow Distance Acceptance]: Decimal128 negative
# values that underflow to double -0.0 are accepted as maxDistance and
# minDistance because the converted double value is nonnegative.
GEONEAR_DECIMAL128_UNDERFLOW_DISTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "max_distance_decimal128_underflow",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": DECIMAL128_MAX_NEGATIVE,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear maxDistance with Decimal128 underflow to -0.0 should be accepted",
    ),
    StageTestCase(
        "min_distance_decimal128_underflow",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": DECIMAL128_MAX_NEGATIVE,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear minDistance with Decimal128 underflow to -0.0 should be accepted",
    ),
]

# Property [No Default Limit]: $geoNear returns all matching documents when no
# explicit limit is applied.
GEONEAR_NO_DEFAULT_LIMIT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "no_default_limit",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": i, "loc": {"type": "Point", "coordinates": [i * 0.01, 0]}} for i in range(101)
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            },
            {"$project": {"_id": 1}},
        ],
        expected=[{"_id": i} for i in range(101)],
        msg="$geoNear should return all 101 documents without a default limit",
    ),
]

# Property [Empty Collection]: $geoNear on an existing collection with a
# geospatial index but no documents returns an empty result set.
GEONEAR_EMPTY_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_collection",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[],
        msg="$geoNear on an empty collection should return no documents",
    ),
]

GEONEAR_DISTANCE_CALCULATION_TESTS = (
    GEONEAR_ORDERING_TESTS
    + GEONEAR_GEOJSON_METERS_TESTS
    + GEONEAR_LEGACY_RADIANS_TESTS
    + GEONEAR_LEGACY_PLANAR_TESTS
    + GEONEAR_PERIMETER_DISTANCE_TESTS
    + GEONEAR_SPHERICAL_COERCION_TESTS
    + GEONEAR_DECIMAL128_UNDERFLOW_DISTANCE_TESTS
    + GEONEAR_NO_DEFAULT_LIMIT_TESTS
    + GEONEAR_EMPTY_COLLECTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_DISTANCE_CALCULATION_TESTS))
def test_geoNear_distance_calculation(collection, test_case: StageTestCase):
    """Test $geoNear distance calculation behavior."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
