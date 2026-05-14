"""Tests for $geoNear output field configuration."""

from __future__ import annotations

from functools import reduce
from typing import Any, cast

import pytest
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ZERO

# Property [distanceField Omitted]: when distanceField is omitted, the output
# documents contain no computed distance field.
GEONEAR_DISTANCE_FIELD_OMITTED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_field_omitted",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "spherical": True,
                }
            }
        ],
        expected=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        msg="$geoNear with distanceField omitted should produce no distance field",
    ),
]

# Property [distanceField Dot Notation]: distanceField with dot notation
# creates a nested output document at the specified path.
GEONEAR_DISTANCE_FIELD_DOT_NOTATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_field_dot_notation",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "a.b",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": {"b": DOUBLE_ZERO},
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": {"b": 111_318.84502145034},
            },
        ],
        msg="$geoNear distanceField with dot notation should create nested output",
    ),
    StageTestCase(
        "distance_field_numeric_dot_notation",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "a.0",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": {"0": DOUBLE_ZERO},
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": {"0": 111_318.84502145034},
            },
        ],
        msg=(
            "$geoNear distanceField with numeric path component should"
            " create nested object with string key, not array"
        ),
    ),
    StageTestCase(
        "distance_field_numeric_dot_notation_nested",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "a.0.b",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": {"0": {"b": DOUBLE_ZERO}},
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "a": {"0": {"b": 111_318.84502145034}},
            },
        ],
        msg=(
            "$geoNear distanceField with numeric path component followed by"
            " field name should create nested objects with string keys"
        ),
    ),
    StageTestCase(
        "distance_field_numeric_dot_notation_overwrites_array",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": ["existing"],
            },
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "a.0",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a": {"0": DOUBLE_ZERO},
            },
        ],
        msg=(
            "$geoNear distanceField with numeric path component should"
            " overwrite existing array with nested object"
        ),
    ),
]

# Property [includeLocs Overwrites distanceField]: when includeLocs and
# distanceField are set to the same path, includeLocs overwrites the distance
# value.
GEONEAR_INCLUDE_LOCS_OVERWRITES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "include_locs_overwrites_distance_field",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
            {"_id": 2, "loc": {"type": "Point", "coordinates": [1, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "info",
                    "includeLocs": "info",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "info": {"type": "Point", "coordinates": [0, 0]},
            },
            {
                "_id": 2,
                "loc": {"type": "Point", "coordinates": [1, 0]},
                "info": {"type": "Point", "coordinates": [1, 0]},
            },
        ],
        msg=(
            "$geoNear with includeLocs and distanceField on the same path"
            " should have includeLocs overwrite the distance value"
        ),
    ),
]

# Property [$meta geoNearDistance and geoNearPoint]: $meta
# "geoNearDistance" returns the computed distance and $meta
# "geoNearPoint" returns the matched location in a subsequent stage.
GEONEAR_META_SUPPORT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "meta_geo_near_distance",
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
            },
            {
                "$project": {
                    "metaDist": {"$meta": "geoNearDistance"},
                    "dist": 1,
                }
            },
        ],
        expected=[
            {"_id": 1, "dist": DOUBLE_ZERO, "metaDist": DOUBLE_ZERO},
            {
                "_id": 2,
                "dist": 111_318.84502145034,
                "metaDist": 111_318.84502145034,
            },
        ],
        msg='$meta "geoNearDistance" should return the computed distance in a subsequent stage',
    ),
    StageTestCase(
        "meta_geo_near_point",
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
            },
            {
                "$project": {
                    "metaPoint": {"$meta": "geoNearPoint"},
                    "dist": 1,
                }
            },
        ],
        expected=[
            {
                "_id": 1,
                "dist": DOUBLE_ZERO,
                "metaPoint": {"type": "Point", "coordinates": [0, 0]},
            },
            {
                "_id": 2,
                "dist": 111_318.84502145034,
                "metaPoint": {"type": "Point", "coordinates": [1, 0]},
            },
        ],
        msg='$meta "geoNearPoint" should return the matched location in a subsequent stage',
    ),
]

# Property [distanceField Path Validation - Accepted]: distanceField
# accepts dot-separated paths up to 199 components.
GEONEAR_DISTANCE_FIELD_PATH_ACCEPTED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_field_depth_199",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": ".".join(["a"] * 199),
                    "spherical": True,
                }
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                **reduce(lambda v, k: {k: v}, reversed(["a"] * 199), cast(Any, DOUBLE_ZERO)),
            },
        ],
        msg="$geoNear distanceField with 199-component path should succeed",
    ),
]

# Property [includeLocs Path Validation - Accepted]: includeLocs accepts
# dot-separated paths up to 199 components.
GEONEAR_INCLUDE_LOCS_PATH_ACCEPTED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "include_locs_depth_199",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": ".".join(["a"] * 199),
                    "spherical": True,
                }
            },
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "dist": DOUBLE_ZERO,
                **reduce(
                    lambda v, k: {k: v},
                    reversed(["a"] * 199),
                    cast(Any, {"type": "Point", "coordinates": [0, 0]}),
                ),
            },
        ],
        msg="$geoNear includeLocs with 199-component path should succeed",
    ),
]

# Property [distanceField Unicode Dot-Like Characters]: Unicode characters
# that visually resemble a dot (U+2024, U+FF0E) are not treated as path
# separators and produce a single top-level field.
GEONEAR_DISTANCE_FIELD_UNICODE_DOT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_field_unicode_one_dot_leader",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "a\u2024b",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a\u2024b": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear distanceField with U+2024 should not split the path",
    ),
    StageTestCase(
        "distance_field_unicode_fullwidth_stop",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "a\uff0eb",
                    "spherical": True,
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "a\uff0eb": DOUBLE_ZERO,
            },
        ],
        msg="$geoNear distanceField with U+FF0E should not split the path",
    ),
]

GEONEAR_OUTPUT_FIELDS_TESTS = (
    GEONEAR_DISTANCE_FIELD_OMITTED_TESTS
    + GEONEAR_DISTANCE_FIELD_DOT_NOTATION_TESTS
    + GEONEAR_INCLUDE_LOCS_OVERWRITES_TESTS
    + GEONEAR_META_SUPPORT_TESTS
    + GEONEAR_DISTANCE_FIELD_PATH_ACCEPTED_TESTS
    + GEONEAR_INCLUDE_LOCS_PATH_ACCEPTED_TESTS
    + GEONEAR_DISTANCE_FIELD_UNICODE_DOT_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_OUTPUT_FIELDS_TESTS))
def test_geoNear_output_fields(collection, test_case: StageTestCase):
    """Test $geoNear output field configuration."""
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
