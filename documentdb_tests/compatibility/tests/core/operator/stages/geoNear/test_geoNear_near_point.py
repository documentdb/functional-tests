"""Tests for $geoNear near point acceptance and index resolution."""

from __future__ import annotations

import pytest
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
    DECIMAL128_ZERO,
    DOUBLE_ZERO,
)

# Property [GeoJSON Near Point Acceptance]: a GeoJSON near point is accepted
# when it represents a valid Point geometry.
GEONEAR_GEOJSON_NEAR_POINT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "geojson_boundary_lon_lat",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [180, 90]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": 10_018_696.051930532,
            },
        ],
        msg="$geoNear with GeoJSON boundary lon=180, lat=90 should succeed",
    ),
    StageTestCase(
        "geojson_boundary_negative_lon_lat",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [-180, -90]},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": 10_018_696.051930532,
            },
        ],
        msg="$geoNear with GeoJSON boundary lon=-180, lat=-90 should succeed",
    ),
    StageTestCase(
        "geojson_3d_coordinates",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0, 100]},
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
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear with 3D GeoJSON coordinates should ignore the third element",
    ),
    StageTestCase(
        "geojson_missing_type_field",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"coordinates": [0, 0]},
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
                "dist": 111_318.84502145034,
            },
        ],
        msg=(
            "$geoNear with missing type field but coordinates present"
            " should be treated as GeoJSON Point"
        ),
    ),
    StageTestCase(
        "geojson_coordinates_as_object",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": {"a": 1, "b": 0}},
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear with coordinates as object should use values in field order as [lon, lat]",
    ),
    StageTestCase(
        "geojson_near_decimal128_coordinates",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [DECIMAL128_ZERO, DECIMAL128_ZERO],
                    },
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
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear with Decimal128 coordinates in GeoJSON near should produce correct distances",
    ),
]

# Property [Legacy Near Point Acceptance]: legacy [lon, lat] coordinate
# arrays are accepted as the near point with both 2d and 2dsphere indexes.
GEONEAR_LEGACY_NEAR_POINT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "legacy_2d_boundary_max",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [180, 180], "distanceField": "dist", "spherical": False}}],
        expected=[
            {"_id": 1, "loc": [0, 0], "dist": 254.55844122715712},
        ],
        msg="$geoNear with legacy near [180, 180] and 2d index should succeed",
    ),
    StageTestCase(
        "legacy_2d_boundary_min",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[
            {"$geoNear": {"near": [-180, -180], "distanceField": "dist", "spherical": False}}
        ],
        expected=[
            {"_id": 1, "loc": [0, 0], "dist": 254.55844122715712},
        ],
        msg="$geoNear with legacy near [-180, -180] and 2d index should succeed",
    ),
    StageTestCase(
        "legacy_2dsphere_boundary_max",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [180, 90], "distanceField": "dist", "spherical": True}}],
        expected=[
            {"_id": 1, "loc": [0, 0], "dist": 1.5707963267948968},
        ],
        msg="$geoNear with legacy near [180, 90] and 2dsphere+spherical should succeed",
    ),
    StageTestCase(
        "legacy_2dsphere_boundary_min",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[{"$geoNear": {"near": [-180, -90], "distanceField": "dist", "spherical": True}}],
        expected=[
            {"_id": 1, "loc": [0, 0], "dist": 1.5707963267948968},
        ],
        msg="$geoNear with legacy near [-180, -90] and 2dsphere+spherical should succeed",
    ),
    StageTestCase(
        "legacy_2d_decimal128_precision_loss",
        indexes=[IndexModel([("loc", "2d")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": [Decimal128("180.0000000000000001"), DECIMAL128_ZERO],
                    "distanceField": "dist",
                    "spherical": False,
                }
            }
        ],
        expected=[
            {"_id": 1, "loc": [0, 0], "dist": 180.0},
        ],
        msg=(
            "$geoNear with Decimal128 near value that rounds to 180.0"
            " should pass range check after double conversion"
        ),
    ),
    StageTestCase(
        "legacy_near_decimal128_coordinates",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": [DECIMAL128_ZERO, DECIMAL128_ZERO],
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
                "dist": 0.017453292519943295,
            },
        ],
        msg="$geoNear with Decimal128 coordinates in legacy near should produce correct distances",
    ),
]

# Property [2d Index Preferred Over 2dsphere]: when key is omitted and both
# a 2d and 2dsphere index exist on the same field, the 2d index is selected.
GEONEAR_2D_PREFERRED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "2d_preferred_over_2dsphere",
        indexes=[IndexModel([("loc", "2d")]), IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": [0, 0]},
            {"_id": 2, "loc": [3, 4]},
        ],
        pipeline=[{"$geoNear": {"near": [0, 0], "distanceField": "dist", "spherical": False}}],
        expected=[
            {"_id": 1, "loc": [0, 0], "dist": DOUBLE_ZERO},
            {"_id": 2, "loc": [3, 4], "dist": 5.0},
        ],
        msg=(
            "$geoNear with both 2d and 2dsphere indexes and no key"
            " should prefer the 2d index (planar distances)"
        ),
    ),
]

# Property [Key Dot Notation]: the key parameter with dot notation selects a
# nested geo-indexed field for the distance query.
GEONEAR_KEY_DOT_NOTATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "key_dot_notation_nested_field",
        indexes=[IndexModel([("geo.loc", "2dsphere")])],
        docs=[
            {"_id": 1, "geo": {"loc": {"type": "Point", "coordinates": [0, 0]}}},
            {"_id": 2, "geo": {"loc": {"type": "Point", "coordinates": [1, 0]}}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": "geo.loc",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "geo": {"loc": {"type": "Point", "coordinates": [0, 0]}},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "geo": {"loc": {"type": "Point", "coordinates": [1, 0]}},
                "dist": 111_318.84502145034,
            },
        ],
        msg="$geoNear key with dot notation should select a nested geo-indexed field",
    ),
    StageTestCase(
        "key_numeric_dot_notation",
        indexes=[IndexModel([("geo.0.loc", "2dsphere")])],
        docs=[
            {"_id": 1, "geo": {"0": {"loc": {"type": "Point", "coordinates": [0, 0]}}}},
            {"_id": 2, "geo": {"0": {"loc": {"type": "Point", "coordinates": [1, 0]}}}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": "geo.0.loc",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "geo": {"0": {"loc": {"type": "Point", "coordinates": [0, 0]}}},
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "geo": {"0": {"loc": {"type": "Point", "coordinates": [1, 0]}}},
                "dist": 111_318.84502145034,
            },
        ],
        msg=(
            "$geoNear key with numeric path component should treat it as a"
            " literal string key, not an array index"
        ),
    ),
    StageTestCase(
        "key_numeric_dot_notation_array_traversal",
        indexes=[IndexModel([("geo.0", "2dsphere")])],
        docs=[
            {"_id": 1, "geo": [{"type": "Point", "coordinates": [0, 0]}]},
            {"_id": 2, "geo": [{"type": "Point", "coordinates": [1, 0]}]},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": "geo.0",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "geo": [{"type": "Point", "coordinates": [0, 0]}],
                "dist": DOUBLE_ZERO,
            },
            {
                "_id": 2,
                "geo": [{"type": "Point", "coordinates": [1, 0]}],
                "dist": 111_318.84502145034,
            },
        ],
        msg=(
            "$geoNear key with numeric path component should also"
            " traverse into arrays via index position"
        ),
    ),
]

GEONEAR_NEAR_POINT_TESTS = (
    GEONEAR_GEOJSON_NEAR_POINT_TESTS
    + GEONEAR_LEGACY_NEAR_POINT_TESTS
    + GEONEAR_2D_PREFERRED_TESTS
    + GEONEAR_KEY_DOT_NOTATION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_NEAR_POINT_TESTS))
def test_geoNear_near_point(collection, test_case: StageTestCase):
    """Test $geoNear near point acceptance and index resolution."""
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
