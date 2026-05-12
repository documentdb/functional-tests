"""Tests for $geoNear field path validation errors."""

from __future__ import annotations

import pytest
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FIELD_PATH_DEPTH_LIMIT_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_NULL_BYTE_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    GEO_NEAR_KEY_DEPTH_LIMIT_ERROR,
    GEO_NEAR_MAX_DISTANCE_NOT_CONSTANT_ERROR,
    GEO_NEAR_MIN_DISTANCE_NOT_CONSTANT_ERROR,
    GEO_NEAR_NEAR_NOT_CONSTANT_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
    OVERFLOW_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [distanceField Path Validation - Rejected]: distanceField rejects
# paths that are empty, malformed, or exceed the depth limit.
GEONEAR_DISTANCE_FIELD_INVALID_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "distance_field_empty_string",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$geoNear distanceField with empty string should fail",
    ),
    StageTestCase(
        "distance_field_dollar_prefix",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "$bad",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$geoNear distanceField with $-prefixed string should fail",
    ),
    StageTestCase(
        "distance_field_leading_dot",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": ".bad",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$geoNear distanceField with leading dot should fail",
    ),
    StageTestCase(
        "distance_field_trailing_dot",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "bad.",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$geoNear distanceField with trailing dot should fail",
    ),
    StageTestCase(
        "distance_field_consecutive_dots",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "a..b",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$geoNear distanceField with consecutive dots should fail",
    ),
    StageTestCase(
        "distance_field_null_byte",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "a\x00b",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$geoNear distanceField with null byte should fail",
    ),
    StageTestCase(
        "distance_field_depth_200",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": ".".join(["a"] * 200),
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_DEPTH_LIMIT_ERROR,
        msg="$geoNear distanceField with 200-component path should fail",
    ),
    StageTestCase(
        "distance_field_depth_201",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": ".".join(["a"] * 201),
                    "spherical": True,
                }
            }
        ],
        error_code=OVERFLOW_ERROR,
        msg="$geoNear distanceField with 201-component path should fail with overflow",
    ),
]

# Property [includeLocs Path Validation - Rejected]: includeLocs rejects
# paths that are empty, malformed, or exceed the depth limit.
GEONEAR_INCLUDE_LOCS_INVALID_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "include_locs_empty_string",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": "",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$geoNear includeLocs with empty string should fail",
    ),
    StageTestCase(
        "include_locs_dollar_prefix",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": "$bad",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$geoNear includeLocs with $-prefixed string should fail",
    ),
    StageTestCase(
        "include_locs_leading_dot",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": ".bad",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$geoNear includeLocs with leading dot should fail",
    ),
    StageTestCase(
        "include_locs_trailing_dot",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": "bad.",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$geoNear includeLocs with trailing dot should fail",
    ),
    StageTestCase(
        "include_locs_consecutive_dots",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": "a..b",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$geoNear includeLocs with consecutive dots should fail",
    ),
    StageTestCase(
        "include_locs_null_byte",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": "a\x00b",
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$geoNear includeLocs with null byte should fail",
    ),
    StageTestCase(
        "include_locs_depth_200",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": ".".join(["a"] * 200),
                    "spherical": True,
                }
            }
        ],
        error_code=FIELD_PATH_DEPTH_LIMIT_ERROR,
        msg="$geoNear includeLocs with 200-component path should fail",
    ),
    StageTestCase(
        "include_locs_depth_201",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "includeLocs": ".".join(["a"] * 201),
                    "spherical": True,
                }
            }
        ],
        error_code=OVERFLOW_ERROR,
        msg="$geoNear includeLocs with 201-component path should fail with overflow",
    ),
]

# Property [Key Field Path Validation]: the key parameter rejects paths that
# are empty, malformed, or exceed the depth limit.
GEONEAR_KEY_INVALID_PATH_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "key_depth_180_accepted",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": ".".join(["a"] * 180),
                }
            }
        ],
        error_code=NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="$geoNear key with 180-component path should be accepted",
    ),
    StageTestCase(
        "key_dollar_prefix",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": "$bad",
                }
            }
        ],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$geoNear key with $-prefixed string should fail",
    ),
    StageTestCase(
        "key_leading_dot",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": ".bad",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$geoNear key with leading dot should fail",
    ),
    StageTestCase(
        "key_trailing_dot",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": "bad.",
                }
            }
        ],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$geoNear key with trailing dot should fail",
    ),
    StageTestCase(
        "key_consecutive_dots",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": "a..b",
                }
            }
        ],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$geoNear key with consecutive dots should fail",
    ),
    StageTestCase(
        "key_null_byte",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": "a\x00b",
                }
            }
        ],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$geoNear key with null byte should fail",
    ),
    StageTestCase(
        "key_depth_181",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": ".".join(["a"] * 181),
                }
            }
        ],
        error_code=GEO_NEAR_KEY_DEPTH_LIMIT_ERROR,
        msg="$geoNear key with 181-component path should fail with depth limit error",
    ),
    StageTestCase(
        "key_depth_201",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "key": ".".join(["a"] * 201),
                }
            }
        ],
        error_code=OVERFLOW_ERROR,
        msg="$geoNear key with 201-component path should fail with overflow",
    ),
]

# Property [Non-Constant Expression Arguments]: $geoNear rejects field path
# references and non-constant expressions in near, maxDistance, and minDistance.
GEONEAR_NON_CONSTANT_EXPRESSION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "near_field_path_reference",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": "$loc",
                    "distanceField": "dist",
                    "spherical": True,
                }
            }
        ],
        error_code=GEO_NEAR_NEAR_NOT_CONSTANT_ERROR,
        msg="$geoNear near with field path reference should fail",
    ),
    StageTestCase(
        "max_distance_field_path_reference",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "val": 5,
            },
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "maxDistance": "$val",
                }
            }
        ],
        error_code=GEO_NEAR_MAX_DISTANCE_NOT_CONSTANT_ERROR,
        msg="$geoNear maxDistance with field path reference should fail",
    ),
    StageTestCase(
        "min_distance_field_path_reference",
        indexes=[IndexModel([("loc", "2dsphere")])],
        docs=[
            {
                "_id": 1,
                "loc": {"type": "Point", "coordinates": [0, 0]},
                "val": 5,
            },
        ],
        pipeline=[
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [0, 0]},
                    "distanceField": "dist",
                    "spherical": True,
                    "minDistance": "$val",
                }
            }
        ],
        error_code=GEO_NEAR_MIN_DISTANCE_NOT_CONSTANT_ERROR,
        msg="$geoNear minDistance with field path reference should fail",
    ),
]

GEONEAR_PATH_ERROR_TESTS = (
    GEONEAR_DISTANCE_FIELD_INVALID_PATH_ERROR_TESTS
    + GEONEAR_INCLUDE_LOCS_INVALID_PATH_ERROR_TESTS
    + GEONEAR_KEY_INVALID_PATH_ERROR_TESTS
    + GEONEAR_NON_CONSTANT_EXPRESSION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GEONEAR_PATH_ERROR_TESTS))
def test_geoNear_path_errors(collection, test_case: StageTestCase):
    """Test $geoNear field path validation errors."""
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
